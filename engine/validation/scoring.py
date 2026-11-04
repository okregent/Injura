"""Deterministic reference comparisons; absence of evidence never passes."""

from statistics import mean, pstdev

from engine.squat.recording import recording_gate
from engine.validation.dataset import METRICS, FRAME_METRICS, finite_number


def decision(statuses):
    statuses = list(statuses)
    if any(status not in ('pass', 'fail', 'not_evaluated') for status in statuses):
        raise ValueError('unsupported evaluation decision')
    return 'fail' if 'fail' in statuses else 'not_evaluated' if not statuses or 'not_evaluated' in statuses else 'pass'


def match_cycles(predictions, references, minimum_iou=.5):
    """Chronological references; greatest eligible overlap, earlier prediction tie."""
    matches, previous = {}, -1
    for reference_index, reference in enumerate(references):
        options = []
        for index, prediction in enumerate(predictions):
            if index <= previous:
                continue
            intersection = max(0, min(prediction['end_source'], reference['end_source'])
                               - max(prediction['start_source'], reference['start_source']))
            union = ((prediction['end_source'] - prediction['start_source'])
                     + (reference['end_source'] - reference['start_source']) - intersection)
            iou = intersection / union if union > 0 else 0
            if iou >= minimum_iou:
                options.append((iou, -index, index))
        if options:
            chosen = max(options)[2]
            matches[reference_index] = chosen
            previous = chosen
    return matches


def summarize_pairs(pairs, limits, minimum_coverage=.9, minimum_samples=1):
    """Missing predictions remain in denominator; unresolved references are pending."""
    if len(pairs) < minimum_samples or any(not finite_number(pair.get('reference')) for pair in pairs):
        return dict(status='not_evaluated', expected=len(pairs), ready=0,
                    reason='independent reference quota/values incomplete', pairs=pairs)
    errors = [pair['observed'] - pair['reference'] for pair in pairs
              if pair.get('ready') is True and finite_number(pair.get('observed'))]
    coverage = len(errors) / len(pairs) if pairs else 0
    mae = mean(abs(error) for error in errors) if errors else None
    maximum = max((abs(error) for error in errors), default=None)
    passed = coverage >= minimum_coverage and maximum is not None
    if 'max_mean_absolute_error' in limits:
        passed = passed and mae <= limits['max_mean_absolute_error']
    if 'max_absolute_error' in limits:
        passed = passed and maximum <= limits['max_absolute_error']
    return dict(status='pass' if passed else 'fail', expected=len(pairs), ready=len(errors),
                coverage=coverage, mean_signed_error=mean(errors) if errors else None,
                mean_absolute_error=mae, max_absolute_error=maximum, pairs=pairs)


def observed_outcome(analysis, rep_index, name, review):
    metric, attribute = METRICS.get(name, ('timing', 'total_seconds'))
    status, reason = recording_gate(metric, review, analysis.features.side)
    if rep_index is None:
        return None, False, 'reference repetition unmatched'
    outcome = analysis.repetitions[rep_index].metrics.get(metric)
    value = getattr(outcome.value, attribute, None) if outcome and attribute else outcome.value if outcome else None
    if status != 'approved':
        return value if finite_number(value) else None, False, reason
    if analysis.calibration_method.endswith('_experimental'):
        return value, False, 'experimental calibration'
    if outcome is None or outcome.quality.status != 'available' or outcome.quality.recovered_frames:
        return value if finite_number(value) else None, False, outcome.quality.reason if outcome else 'metric missing'
    return value if finite_number(value) else None, finite_number(value), None if finite_number(value) else 'numeric value unavailable'


def frame_observation(analysis, extraction, source, name, review):
    status, reason = recording_gate(METRICS[name][0], review, analysis.features.side)
    if status != 'approved':
        return None, False, reason
    try:
        index = extraction.source_frame_indices.index(source)
    except ValueError:
        return None, False, 'source frame not detected'
    attribute, mask = {'knee_flexion': ('knee_angles', 'knee_angle'),
                       'hip_flexion': ('hip_angles', 'hip_angle'),
                       'torso_lean': ('torso_angles', 'torso_angle')}[name]
    value = getattr(analysis.features, attribute)[index]
    ready = (analysis.features.valid_masks[mask][index] and finite_number(value)
             and source not in extraction.recovered_frame_indices
             and not analysis.calibration_method.endswith('_experimental'))
    return value, bool(ready), None if ready else 'frame observations require review'


def score_compliant(analysis, extraction, reference, review, limits):
    """References must already pass dataset eligibility and uncertainty checks."""
    required = ['complete_repetitions', 'start_boundary', 'end_boundary', 'deepest_observed_frame',
                'total_duration', *METRICS, 'consistency']
    if (reference.get('confirmed') is not True or reference.get('origin') != 'independent_review'
            or not reference.get('reviewer') or not reference.get('repetitions')):
        return dict(status='not_evaluated', metrics={name: dict(status='not_evaluated', reason='independent reference unconfirmed')
                                                   for name in required})
    refs = reference['repetitions']
    source = extraction.source_frame_indices
    predictions = [dict(start_source=source[rep.rep.start_index], end_source=source[rep.rep.end_index])
                   for rep in analysis.repetitions]
    matches = match_cycles(predictions, refs, limits['metrics']['complete_repetitions']['minimum_matching_temporal_iou'])
    missed, spurious = len(refs) - len(matches), len(predictions) - len(matches)
    count_limits = limits['metrics']['complete_repetitions']
    report = {'complete_repetitions': dict(status='pass' if missed <= count_limits['max_missed_per_compliant_clip']
                                          and spurious <= count_limits['max_spurious_per_compliant_clip'] and refs else 'fail',
                                          references=len(refs), detected=len(predictions), missed=missed, spurious=spurious,
                                          excluded_candidates=len(analysis.candidates), matches=matches)}
    coverage = limits['coverage']['minimum_interpretation_ready_fraction_per_metric_per_compliant_clip']
    for name in ('start_boundary', 'end_boundary', 'deepest_observed_frame', 'total_duration'):
        pairs = []
        for i, ref in enumerate(refs):
            index = matches.get(i)
            observed, ready, reason = observed_outcome(analysis, index, 'total_duration' if name == 'total_duration' else 'relative_descent', review)
            if name == 'total_duration':
                expected = (ref['end_source'] - ref['start_source']) / extraction.fps if extraction.fps else None
            elif name == 'deepest_observed_frame':
                expected = 0
                if index is not None and observed is not None:
                    deepest = analysis.repetitions[index].metrics['depth'].value
                    frame = source[deepest.deepest_index]
                    low, high = ref['deepest_interval']
                    observed = frame - low if frame < low else frame - high if frame > high else 0
            else:
                field = 'start_source' if name == 'start_boundary' else 'end_source'
                expected = ref[field]
                observed = predictions[index][field] if index is not None else None
            pairs.append(dict(reference_id=i + 1, reference=expected, observed=observed, ready=ready, reason=reason))
        maximum = (limits['metrics'][name].get('max_absolute_error_frames')
                   or limits['metrics'][name].get('max_distance_from_reference_interval_frames'))
        if name == 'total_duration':
            maximum = limits['metrics'][name]['max_absolute_error_source_intervals'] / extraction.fps if extraction.fps else 0
        report[name] = summarize_pairs(pairs, {'max_absolute_error': maximum}, coverage)
    for name in METRICS:
        pairs = []
        for i, ref in enumerate(refs):
            observed, ready, reason = observed_outcome(analysis, matches.get(i), name, review)
            item = ref.get('metrics', {}).get(name, {})
            pairs.append(dict(reference_id=i + 1, reference=item.get('value'), observed=observed, ready=ready, reason=reason))
        measured = summarize_pairs(pairs, limits['metrics'][name], coverage)
        if name in FRAME_METRICS:
            frame_pairs = []
            for item in reference.get('frame_measurements', []):
                if item.get('metric') != name:
                    continue
                observed, ready, reason = frame_observation(analysis, extraction, item['source_frame'], name, review)
                frame_pairs.append(dict(source_frame=item['source_frame'], reference=item.get('value'),
                                        observed=observed, ready=ready, reason=reason))
            framewise = summarize_pairs(frame_pairs, limits['metrics'][name], coverage,
                                       limits['coverage']['minimum_preselected_reference_frames_per_framewise_metric_per_compliant_clip'])
            report[name] = dict(status=decision((measured['status'], framewise['status'])),
                                repetition_outcomes=measured, framewise=framewise)
        else:
            report[name] = measured
    consistency_errors = []
    for metric, attribute, prerequisite in [('depth', 'depth_ratio', 'relative_descent'),
            ('torso_lean', 'max_lean_angle', 'torso_lean'), ('knee_travel', 'max_travel', 'raw_knee_travel'),
            ('normalized_knee_travel', 'normalized_travel', 'foot_normalized_knee_travel'), ('timing', 'total_seconds', 'total_duration')]:
        values = [getattr(rep.metrics[metric].value, attribute) for rep in analysis.repetitions if rep.metrics[metric].value is not None]
        values = [value for value in values if finite_number(value)]
        result = analysis.consistency.get(metric)
        expected = dict(valid_count=len(values), total_count=len(analysis.repetitions),
                        mean=mean(values) if values else None, standard_deviation=pstdev(values) if len(values) > 1 else None,
                        value_range=max(values) - min(values) if len(values) > 1 else None)
        for field, value in expected.items():
            actual = getattr(result, field, None)
            if (value is None) != (actual is None) or (value is not None and (not finite_number(actual)
                    or abs(value - actual) > limits['metrics']['consistency']['recomputation_absolute_tolerance'])):
                consistency_errors.append(f'{metric}.{field}')
    prerequisites = [report[name]['status'] for name in ('relative_descent', 'torso_lean', 'raw_knee_travel', 'foot_normalized_knee_travel', 'total_duration')]
    report['consistency'] = dict(status='fail' if consistency_errors else 'pass' if all(item == 'pass' for item in prerequisites) else 'not_evaluated',
                                 recomputation_errors=consistency_errors, reason='requires validated constituent measures')
    phase_checks = []
    for number, rep in enumerate(analysis.repetitions, 1):
        timing = rep.metrics['timing'].value
        values = ([timing.descent_seconds, timing.bottom_seconds, timing.ascent_seconds, timing.total_seconds]
                  if timing is not None else [])
        status = ('not_evaluated' if not values or not all(finite_number(value) for value in values)
                  else 'pass' if abs(sum(values[:3]) - values[3]) <= limits['metrics']['phase_duration']['sum_tolerance_seconds'] else 'fail')
        phase_checks.append(dict(repetition=number, status=status))
    report['phase_duration_arithmetic'] = dict(status=decision(item['status'] for item in phase_checks),
                                              repetitions=phase_checks, scope='arithmetic only; physical phase events remain unvalidated')
    return dict(status=decision(item['status'] for item in report.values()), metrics=report,
                restricted_items={'phase_duration': 'physical event semantics unvalidated', 'heel_rise_duration': 'event reference undefined'})


def score_violation(analysis, review, affected, unaffected):
    evidence = []
    for expected, names in ((False, affected), (True, unaffected)):
        for name in names:
            metric = METRICS.get(name, ('timing', None))[0]
            status, reason = recording_gate(metric, review, analysis.features.side)
            gate_ready = status == 'approved'
            evidence.append(dict(metric=name, expected_gate_approved=expected, actual_gate_status=status,
                                 reason=reason, status='pass' if gate_ready == expected else 'fail'))
    # Raw analysis is neither changed nor converted into posture feedback.
    return dict(status=decision(item['status'] for item in evidence), eligibility_checks=evidence,
                raw_repetitions=len(analysis.repetitions), candidates=len(analysis.candidates),
                scope='human-review item isolation; not an automatic camera detector benchmark')

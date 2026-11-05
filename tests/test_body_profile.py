from dataclasses import replace

import pytest

from engine.squat.profile import BodyProfile, ProjectedLength, load_profile, save_profile, summarize_profile


def profile():
    return BodyProfile('example', 'a' * 64, 0, 'left', 'front',
                       ProjectedLength(100, 2), ProjectedLength(80, 2), ProjectedLength(120, 3),
                       reviewer='fixture', upright=True, camera_level=True, joints_visible=True, body_aligned=True)


def test_reviewed_ratios_and_conservative_bounds():
    result = summarize_profile(profile(), source_sha256='a' * 64)
    ratio = result['ratios']['thigh_to_shank']
    assert ratio['value'] == 1.25
    assert ratio['lower'] == 98 / 82 and ratio['upper'] == 102 / 78
    assert result['accuracy_status'] == 'not_validated'
    assert result['coaching_status'] == 'pending_validation'


@pytest.mark.parametrize('changes,status', [({'reviewer': None}, 'review_required'),
    ({'upright': None}, 'review_required'), ({'body_aligned': False}, 'rejected')])
def test_unreviewed_or_rejected_capture_withholds_ratios(changes, status):
    result = summarize_profile(replace(profile(), **changes), source_sha256='a' * 64)
    assert result['status'] == status and result['ratios'] == {}


@pytest.mark.parametrize('value,uncertainty', [(0, 0), (1, 1), (1, -1), (True, 0), (float('nan'), 0)])
def test_invalid_lengths_rejected(value, uncertainty):
    with pytest.raises(ValueError):
        ProjectedLength(value, uncertainty)


def test_roundtrip_preserves_review_and_refuses_overwrite(tmp_path):
    path = tmp_path / 'profile.json'
    save_profile(profile(), path)
    assert load_profile(path) == profile()
    with pytest.raises(FileExistsError):
        save_profile(profile(), path)
    with pytest.raises(ValueError, match='mismatch'):
        summarize_profile(profile(), source_sha256='b' * 64)


@pytest.mark.parametrize('changes', [dict(source_frame=True), dict(side='auto'), dict(source_sha256='bad'),
                                   dict(camera_level=1), dict(schema_version=2)])
def test_invalid_profile_metadata_rejected(changes):
    with pytest.raises(ValueError):
        replace(profile(), **changes)

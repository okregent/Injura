"""Source-bound projected body proportions; no anatomical or coaching claims."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ProjectedLength:
    pixels: float
    uncertainty_pixels: float

    def __post_init__(self):
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) for value in (self.pixels, self.uncertainty_pixels)):
            raise ValueError('length and uncertainty must be finite numbers')
        if self.pixels <= 0 or not 0 <= self.uncertainty_pixels < self.pixels:
            raise ValueError('length must remain positive throughout its uncertainty interval')


@dataclass(frozen=True)
class BodyProfile:
    profile_id: str
    source_sha256: str
    source_frame: int
    side: str
    view: str
    thigh: ProjectedLength
    shank: ProjectedLength
    torso: ProjectedLength
    reviewer: Optional[str] = None
    upright: Optional[bool] = None
    camera_level: Optional[bool] = None
    joints_visible: Optional[bool] = None
    body_aligned: Optional[bool] = None
    schema_version: int = 1

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError('unsupported profile schema')
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise ValueError('profile id required')
        if (not isinstance(self.source_sha256, str) or len(self.source_sha256) != 64
                or any(char not in '0123456789abcdef' for char in self.source_sha256)):
            raise ValueError('lowercase SHA-256 source hash required')
        if type(self.source_frame) is not int or self.source_frame < 0:
            raise ValueError('nonnegative source frame required')
        if self.side not in ('left', 'right') or self.view not in ('front', 'side'):
            raise ValueError('explicit side and front/side view required')
        if any(not isinstance(value, ProjectedLength) for value in (self.thigh, self.shank, self.torso)):
            raise ValueError('projected segment lengths required')
        if self.reviewer is not None and (not isinstance(self.reviewer, str) or not self.reviewer.strip()):
            raise ValueError('reviewer must be nonempty or null')
        if any(value is not None and type(value) is not bool for value in
               (self.upright, self.camera_level, self.joints_visible, self.body_aligned)):
            raise ValueError('capture checks must be boolean or null')


def load_profile(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('profile object required')
    try:
        return BodyProfile(**{**data, **{name: ProjectedLength(**data[name]) for name in ('thigh', 'shank', 'torso')}})
    except (KeyError, TypeError) as error:
        raise ValueError('invalid profile fields') from error


def save_profile(profile, path):
    """Never overwrite an earlier personal measurement."""
    if not isinstance(profile, BodyProfile):
        raise ValueError('BodyProfile required')
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(asdict(profile), handle, indent=2, allow_nan=False)


def summarize_profile(profile, *, source_sha256):
    """Ratios describe same-frame image segments only; bounds are not confidence."""
    if source_sha256 != profile.source_sha256:
        raise ValueError('profile source content mismatch')
    checks = (profile.upright, profile.camera_level, profile.joints_visible, profile.body_aligned)
    status = ('rejected' if False in checks else 'review_required'
              if not profile.reviewer or any(value is None for value in checks) else 'reviewed_projection')
    ratios = {}
    if status == 'reviewed_projection':
        leg = ProjectedLength(profile.thigh.pixels + profile.shank.pixels,
                              profile.thigh.uncertainty_pixels + profile.shank.uncertainty_pixels)
        for name, numerator, denominator in (
                ('thigh_to_shank', profile.thigh, profile.shank),
                ('torso_to_thigh', profile.torso, profile.thigh),
                ('torso_to_leg', profile.torso, leg)):
            ratios[name] = dict(value=numerator.pixels / denominator.pixels,
                lower=(numerator.pixels - numerator.uncertainty_pixels) / (denominator.pixels + denominator.uncertainty_pixels),
                upper=(numerator.pixels + numerator.uncertainty_pixels) / (denominator.pixels - denominator.uncertainty_pixels))
    return dict(profile_id=profile.profile_id, status=status, ratios=ratios,
                measurement_scope='same-frame 2D projected segment ratios; not bone lengths',
                accuracy_status='not_validated', coaching_status='pending_validation')

"""Explicit repository paths and containment checks for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from .errors import ConfigurationError, InputMissingError


_RELEASE_VERSION = re.compile(r"V[0-9]+\.[0-9]+")


def _require_path(value: Path) -> Path:
    if not isinstance(value, Path):
        raise TypeError("pipeline paths must be pathlib.Path values")
    return value.resolve(strict=False)


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


@dataclass(frozen=True)
class PipelineConfig:
    repo_root: Path
    staging_root: Path = field(init=False)
    releases_root: Path = field(init=False)
    baselines_root: Path = field(init=False)

    def __post_init__(self) -> None:
        repo_root = _require_path(self.repo_root)
        staging_root = (repo_root / "data" / "staging").resolve(strict=False)
        releases_root = (repo_root / "releases").resolve(strict=False)
        baselines_root = (repo_root / "data" / "baselines").resolve(strict=False)

        roots = (
            ("staging", staging_root),
            ("releases", releases_root),
            ("baselines", baselines_root),
        )
        for index, (first_name, first) in enumerate(roots):
            for second_name, second in roots[index + 1 :]:
                if _paths_overlap(first, second):
                    raise ConfigurationError(
                        f"{first_name} and {second_name} roots must not overlap"
                    )

        object.__setattr__(self, "repo_root", repo_root)
        object.__setattr__(self, "staging_root", staging_root)
        object.__setattr__(self, "releases_root", releases_root)
        object.__setattr__(self, "baselines_root", baselines_root)

    def require_staging_output(self, path: Path) -> Path:
        resolved = _require_path(path)
        if not resolved.is_relative_to(self.staging_root):
            raise ConfigurationError("output path must remain inside the staging root")
        return resolved

    def require_release_input(self, path: Path) -> Path:
        resolved = _require_path(path)
        if not resolved.is_relative_to(self.releases_root):
            raise ConfigurationError("input path must remain inside the releases root")
        if not resolved.exists():
            raise InputMissingError(f"release input does not exist: {resolved}")
        return resolved

    def new_formal_target(self, release_version: str) -> Path:
        if _RELEASE_VERSION.fullmatch(release_version) is None:
            raise ConfigurationError(f"invalid release version: {release_version!r}")
        if release_version == "V1.18":
            raise ConfigurationError("the frozen V1.18 release cannot be replaced")
        target = (self.releases_root / release_version).resolve(strict=False)
        if not target.is_relative_to(self.releases_root):
            raise ConfigurationError("formal target must remain inside the releases root")
        if target.exists():
            raise ConfigurationError(f"formal target already exists: {target}")
        return target

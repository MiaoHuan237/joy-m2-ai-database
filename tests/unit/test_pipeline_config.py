from __future__ import annotations

import importlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def load_contract(test: unittest.TestCase):
    importlib.invalidate_caches()
    try:
        config_module = importlib.import_module("joy_m2.config")
        errors_module = importlib.import_module("joy_m2.errors")
    except ModuleNotFoundError as error:
        test.fail(f"required pipeline interface module is not implemented: {error.name}")
    return config_module.PipelineConfig, errors_module


class PipelineConfigContractTests(unittest.TestCase):
    ROOT_PATHS = {
        "staging": Path("data/staging"),
        "releases": Path("releases"),
        "baselines": Path("data/baselines"),
    }

    def make_repository(self, base: Path) -> Path:
        root = base / "repository"
        (root / "data" / "staging").mkdir(parents=True)
        (root / "data" / "baselines" / "V1.18").mkdir(parents=True)
        (root / "releases" / "V1.18").mkdir(parents=True)
        return root

    def assert_overlap_rejected(self, first_name: str, second_name: str) -> None:
        PipelineConfig, errors = load_contract(self)
        for relation in ("same", "first_contains_second", "second_contains_first"):
            with self.subTest(first=first_name, second=second_name, relation=relation):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp) / "repository"
                    first = root / self.ROOT_PATHS[first_name]
                    second = root / self.ROOT_PATHS[second_name]
                    third_name = next(
                        name for name in self.ROOT_PATHS if name not in {first_name, second_name}
                    )
                    third = root / self.ROOT_PATHS[third_name]
                    third.mkdir(parents=True)
                    if relation == "same":
                        first.mkdir(parents=True)
                        second.parent.mkdir(parents=True, exist_ok=True)
                        second.symlink_to(first, target_is_directory=True)
                    elif relation == "first_contains_second":
                        nested = first / "nested-second"
                        nested.mkdir(parents=True)
                        second.parent.mkdir(parents=True, exist_ok=True)
                        second.symlink_to(nested, target_is_directory=True)
                    else:
                        nested = second / "nested-first"
                        nested.mkdir(parents=True)
                        first.parent.mkdir(parents=True, exist_ok=True)
                        first.symlink_to(nested, target_is_directory=True)
                    with self.assertRaises(errors.ConfigurationError):
                        PipelineConfig(root)

    def test_repository_and_derived_roots_are_resolved_absolute_paths(self) -> None:
        PipelineConfig, _ = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            self.assertEqual(config.repo_root, root.resolve())
            self.assertEqual(config.staging_root, (root / "data" / "staging").resolve())
            self.assertEqual(config.releases_root, (root / "releases").resolve())
            self.assertEqual(config.baselines_root, (root / "data" / "baselines").resolve())

    def test_staging_output_is_resolved_only_inside_staging(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            wanted = root / "data" / "staging" / "run-1" / "artifact.json"
            self.assertEqual(config.require_staging_output(wanted), wanted.resolve())
            with self.assertRaises(errors.ConfigurationError):
                config.require_staging_output(root / "outside.json")

    def test_parent_traversal_cannot_escape_staging(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            with self.assertRaises(errors.ConfigurationError):
                config.require_staging_output(root / "data" / "staging" / ".." / "escaped.json")

    def test_output_symlink_cannot_escape_staging(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_repository(base)
            outside = base / "outside"
            outside.mkdir()
            (root / "data" / "staging" / "link").symlink_to(outside, target_is_directory=True)
            config = PipelineConfig(root)
            with self.assertRaises(errors.ConfigurationError):
                config.require_staging_output(root / "data" / "staging" / "link" / "file")

    def test_staging_and_release_roots_reject_same_and_nested_paths(self) -> None:
        self.assert_overlap_rejected("staging", "releases")

    def test_staging_and_baseline_roots_reject_same_and_nested_paths(self) -> None:
        self.assert_overlap_rejected("staging", "baselines")

    def test_release_and_baseline_roots_reject_same_and_nested_paths(self) -> None:
        self.assert_overlap_rejected("releases", "baselines")

    def test_formal_target_rejects_v118_and_invalid_versions(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            with self.assertRaises(errors.ConfigurationError):
                config.new_formal_target("V1.18")
            with self.assertRaises(errors.ConfigurationError):
                config.new_formal_target("1.19")

    def test_formal_target_must_not_already_exist(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            (root / "releases" / "V1.19").mkdir()
            config = PipelineConfig(root)
            with self.assertRaises(errors.ConfigurationError):
                config.new_formal_target("V1.19")
            self.assertEqual(config.new_formal_target("V1.20"), (root / "releases" / "V1.20").resolve())

    def test_existing_release_file_and_directory_inputs_are_accepted(self) -> None:
        PipelineConfig, _ = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            release_dir = root / "releases" / "V1.18"
            manifest = release_dir / "manifest.json"
            manifest.write_text("{}\n", encoding="utf-8")
            self.assertEqual(config.require_release_input(release_dir), release_dir.resolve())
            self.assertEqual(config.require_release_input(manifest), manifest.resolve())

    def test_release_input_rejects_parent_traversal_and_prefix_lookalike(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            outside = root / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            lookalike = root / "releases-lookalike" / "manifest.json"
            lookalike.parent.mkdir()
            lookalike.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(errors.ConfigurationError):
                config.require_release_input(root / "releases" / "V1.18" / ".." / ".." / "outside.json")
            with self.assertRaises(errors.ConfigurationError):
                config.require_release_input(lookalike)

    def test_release_input_symlink_cannot_escape_release_root(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_repository(base)
            outside = base / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            link = root / "releases" / "V1.18" / "outside-link.json"
            link.symlink_to(outside)
            config = PipelineConfig(root)
            with self.assertRaises(errors.ConfigurationError):
                config.require_release_input(link)

    def test_missing_release_input_raises_input_missing_error(self) -> None:
        PipelineConfig, errors = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            missing = root / "releases" / "V1.18" / "missing.json"
            with self.assertRaises(errors.InputMissingError):
                config.require_release_input(missing)

    def test_release_input_requires_a_path_value(self) -> None:
        PipelineConfig, _ = load_contract(self)
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_repository(Path(temp))
            config = PipelineConfig(root)
            with self.assertRaises(TypeError):
                config.require_release_input(str(root / "releases" / "V1.18"))


if __name__ == "__main__":
    unittest.main()

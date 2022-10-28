from importlib import import_module
from pathlib import Path

STEPS_FILE_GLOB = "**/*_steps.py"
FEATURE_TEST_DIRNAME = "feature_tests"


def _module_path_from_file_path(file_path: Path):
    path = str(file_path.parent / file_path.stem)
    path_relative_to_api_root = Path(path[path.find(FEATURE_TEST_DIRNAME) :])
    return ".".join(path_relative_to_api_root.parts)


def import_steps_from_subdirs():
    step_file_paths = Path(__file__).parent.glob(STEPS_FILE_GLOB)
    for file_path in step_file_paths:
        module_path = _module_path_from_file_path(file_path)
        import_module(module_path)


import_steps_from_subdirs()

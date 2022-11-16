import shutil
from itertools import chain
from pathlib import Path
from re import Pattern

from common import remove_path_obj
from constants import BASE_API_PATH, LAYER_PATH, SANDBOX_API_PATH, SANDBOX_BUILD_PATH

LAYER_PACKAGE_PATTERN = "*/dist/build/python"
API_PACKAGE_PATTERN = "**/dist/build/"
PATTERNS_TO_REMOVE = ["**/.pytest_cache", "**/scripts", "**/.DS_Store"]


def clean_sandbox_folder():
    if SANDBOX_BUILD_PATH.exists():
        remove_path_obj(path=SANDBOX_BUILD_PATH)
    shutil.copytree(src=BASE_API_PATH, dst=SANDBOX_API_PATH)

    for pattern in PATTERNS_TO_REMOVE:
        for _path in SANDBOX_API_PATH.glob(pattern):
            remove_path_obj(_path)


def _get_path_objs_from_glob(base_path: Path, pattern: Pattern) -> list[Path]:
    path_obj_parents = base_path.glob(pattern)
    return list(chain.from_iterable(map(Path.iterdir, path_obj_parents)))


def copy_layers_to_builds(api_build_paths: list[Path]):
    layer_package_paths = _get_path_objs_from_glob(
        base_path=LAYER_PATH, pattern=LAYER_PACKAGE_PATTERN
    )
    for api_build_path in api_build_paths:
        for layer_pkg_path in layer_package_paths:
            copier = shutil.copytree if layer_pkg_path.is_dir() else shutil.copyfile
            try:
                copier(src=layer_pkg_path, dst=api_build_path / layer_pkg_path.name)
            except:
                continue


def rezip_builds(api_build_paths: list[Path]):
    for api_build_path in api_build_paths:
        build_root = api_build_path.parent
        (zipfile_path,) = build_root.glob("*zip")
        zipfile_path.unlink()
        shutil.make_archive(
            base_name=build_root / zipfile_path.stem,
            format="zip",
            root_dir=api_build_path,
        )


if __name__ == "__main__":
    clean_sandbox_folder()

    api_build_paths = list(SANDBOX_API_PATH.glob(API_PACKAGE_PATTERN))
    copy_layers_to_builds(api_build_paths=api_build_paths)
    rezip_builds(api_build_paths=api_build_paths)

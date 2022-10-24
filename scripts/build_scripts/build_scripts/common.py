import shutil
from functools import cache
from pathlib import Path

DIST_DIR = "dist"
BUILD_DIR = "build"
SCRIPTS_DIR = "scripts"
UNNECESSARY_DIRS = [
    DIST_DIR,
    BUILD_DIR,
    SCRIPTS_DIR,
    "setup.py",
    "__pycache__",
    "*.dist-info",
    "*tests",
    "*.egg-info",
]


@cache
def get_base_dir(file) -> Path:
    return Path(file).parent.parent


def clean_dir(dir_path: Path):
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True)


def zip_package(build_dir: str, format="zip"):
    archive_path = Path(f"{str(build_dir)}.{format}")
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(base_name=build_dir, format=format, root_dir=build_dir)


def copy_source_code(source_dir: Path, build_dir: Path):
    shutil.copytree(
        src=source_dir, dst=build_dir, ignore=shutil.ignore_patterns(*UNNECESSARY_DIRS)
    )

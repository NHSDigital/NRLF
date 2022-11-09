import os
import shutil
import stat
from functools import cache
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

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
PROJECT_ROOT_DIR = str(Path(__file__).parent.parent.parent.parent)


@cache
def get_base_dir(file) -> Path:
    return Path(file).parent.parent


def clean_dir(dir_path: Path):
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True)


def zip_package(build_dir: Path, format="zip"):
    archive_path = Path(f"{str(build_dir)}.{format}")
    if archive_path.exists():
        archive_path.unlink()
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as zip_file:
        for entry in filter(Path.is_file, build_dir.rglob("*")):
            _add_file(zip_file, entry, entry.relative_to(build_dir))


def _add_file(zip_file, path: Path, zip_path: Path):
    permission = 0o555 if os.access(path, os.X_OK) else 0o444
    zip_info = ZipInfo.from_file(path, zip_path)
    zip_info.date_time = (2019, 1, 1, 0, 0, 0)
    zip_info.external_attr = (stat.S_IFREG | permission) << 16
    with open(path, "rb") as fp:
        zip_file.writestr(
            zip_info,
            fp.read(),
            compress_type=ZIP_DEFLATED,
            compresslevel=9,
        )


def copy_source_code(source_dir: Path, build_dir: Path):
    shutil.copytree(
        src=source_dir, dst=build_dir, ignore=shutil.ignore_patterns(*UNNECESSARY_DIRS)
    )

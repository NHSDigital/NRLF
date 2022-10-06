import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from build_scripts.common import (
    get_base_dir,
    clean_dir,
    zip_package,
    DIST_DIR,
    BUILD_DIR,
    copy_source_code,
)


@contextmanager
def create_zip_package(
    package_name: str, base_dir: Path
) -> Generator[Path, None, None]:
    dist_dir = base_dir / DIST_DIR
    build_dir = dist_dir / BUILD_DIR

    clean_dir(dist_dir)

    print(f"Building {package_name}")
    yield build_dir
    zip_package(str(build_dir))
    shutil.move(dist_dir / f"{BUILD_DIR}.zip", dist_dir / f"{package_name}.zip")


def build(file):
    lambda_base_dir = get_base_dir(file)
    package_name = lambda_base_dir.name

    with create_zip_package(
        package_name=package_name, base_dir=lambda_base_dir
    ) as build_dir:
        copy_source_code(source_dir=lambda_base_dir, build_dir=build_dir)

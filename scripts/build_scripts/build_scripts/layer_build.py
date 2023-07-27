import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import sh
from build_scripts.common import (
    BUILD_DIR,
    DIST_DIR,
    clean_dir,
    copy_source_code,
    get_base_dir,
    zip_package,
)

UNNECESSARY_DIRS = [
    "**/__pycache__/*",
    "*.dist-info",
    "*tests",
    "botocore",
    "boto3",
    "**/pydantic/*.so",
    "_pytest",
]


@contextmanager
def create_zip_package(
    package_name: str, base_dir: Path
) -> Generator[Path, None, None]:
    dist_dir = base_dir / DIST_DIR
    build_dir = dist_dir / BUILD_DIR
    package_dir = build_dir / "python"

    clean_dir(dist_dir)

    print(f"Building {package_name}")  # noqa: T201
    yield package_dir
    zip_package(build_dir)
    shutil.move(dist_dir / f"{BUILD_DIR}.zip", dist_dir / f"{package_name}.zip")

    clean_dir(build_dir)


def build(file):
    layer_base_dir = get_base_dir(file)
    package_name = layer_base_dir.name

    with create_zip_package(
        package_name=package_name, base_dir=layer_base_dir
    ) as build_dir:
        copy_source_code(source_dir=layer_base_dir, build_dir=build_dir)


@contextmanager
def create_temp_path(path: Path, is_dir: bool) -> Generator[Path, None, None]:
    error = None
    try:
        if is_dir:
            path.mkdir(parents=True)
        else:
            path.touch()
        yield
    except Exception as err:
        error = err
    finally:
        if is_dir:
            shutil.rmtree(path)
        else:
            path.unlink()
    if error:
        raise error


def clean_unnecessary_files(directory: Path):
    for pattern in UNNECESSARY_DIRS:
        for filename in Path(directory).glob(pattern):
            if filename.is_dir():
                shutil.rmtree(filename)
            else:
                filename.unlink()


def build_third_party(file):
    layer_base_dir = get_base_dir(file)
    package_name = layer_base_dir.name
    root_dir = layer_base_dir.parent.parent

    with create_zip_package(
        package_name=package_name, base_dir=layer_base_dir
    ) as build_dir:
        requirements_txt_path = layer_base_dir / "requirements.txt"
        with create_temp_path(path=requirements_txt_path, is_dir=False):
            requirements = sh.poetry(
                "export", "-f", "requirements.txt", "--without-hashes", _cwd=root_dir
            )
            with open(requirements_txt_path, "w") as f:
                data_split = str(requirements).split("\n")
                f.write("\n".join(data_split[:-1]))
            sh.pip(
                "install",
                "-r",
                requirements_txt_path,
                "--target",
                build_dir,
                _cwd=layer_base_dir,
            )
        clean_unnecessary_files(build_dir)

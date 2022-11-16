import shutil
from pathlib import Path


def remove_path_obj(path: Path):
    remover = shutil.rmtree if path.is_dir() else Path.unlink
    remover(path)

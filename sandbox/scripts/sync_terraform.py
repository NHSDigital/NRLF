import shutil

from common import remove_path_obj
from constants import SANDBOX_TERRAFORM_PATH, TERRAFORM_PATH

PATTERNS_TO_REMOVE = [
    "main.tf",
    ".terraform*",
    "layer.tf",
    "*tfstate",
    "tfplan",
    "**/layer/**/*",
    "sandbox.tf",
]


def clean_terraform_dir():
    SANDBOX_TERRAFORM_PATH.unlink(missing_ok=True)

    shutil.copytree(src=TERRAFORM_PATH, dst=SANDBOX_TERRAFORM_PATH)
    for pattern in PATTERNS_TO_REMOVE:
        for path in SANDBOX_TERRAFORM_PATH.glob(pattern):
            remove_path_obj(path)


def remove_layers_reference_from_lambdas():
    with open(SANDBOX_TERRAFORM_PATH / "lambda.tf", "r") as f:
        lines = list(f.readlines())

    with open(SANDBOX_TERRAFORM_PATH / "lambda.tf", "w") as f:
        for line in lines:
            if "layers" in line:
                line = "  layers                 = null\n"
            f.write(line)


if __name__ == "__main__":
    clean_terraform_dir()
    remove_layers_reference_from_lambdas()

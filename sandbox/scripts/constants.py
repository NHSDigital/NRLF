from pathlib import Path

SANDBOX_PATH = Path(__file__).parent.parent.resolve()
PROJECT_ROOT_PATH = SANDBOX_PATH.parent
BASE_API_PATH = PROJECT_ROOT_PATH / "api"
LAYER_PATH = PROJECT_ROOT_PATH / "layer"
TERRAFORM_PATH = PROJECT_ROOT_PATH / "terraform" / "infrastructure"

SANDBOX_BUILD_PATH = SANDBOX_PATH / "dist"
SANDBOX_API_PATH = SANDBOX_BUILD_PATH / "api"
SANDBOX_TERRAFORM_PATH = SANDBOX_BUILD_PATH / "terraform" / "infrastructure"

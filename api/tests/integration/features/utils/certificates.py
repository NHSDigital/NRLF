from pathlib import Path
from typing import Optional, Tuple

TRUSTSTORE_PATH = Path(__file__).parent / "../../../../../truststore/"
CLIENT_CERT_PATH = TRUSTSTORE_PATH / "client"


def get_cert_path_for_environment(environment: Optional[str]) -> Tuple[str, str]:
    """
    This function returns the certificate for the given environment
    """
    if not environment:
        raise ValueError("Environment (env) not provided")

    cert_path: Optional[Path] = None
    key_path: Optional[Path] = None

    match environment:
        case "dev":
            cert_path = CLIENT_CERT_PATH / "dev.crt"
            key_path = CLIENT_CERT_PATH / "dev.key"

        case _:
            cert_path = CLIENT_CERT_PATH / "dev.crt"
            key_path = CLIENT_CERT_PATH / "dev.key"

    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError(
            f"Client certificate not found at {cert_path} or {key_path}"
        )

    return (str(cert_path.resolve()), str(key_path.resolve()))

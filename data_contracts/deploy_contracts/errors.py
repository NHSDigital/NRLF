import botocore.exceptions


class BadActiveContract(Exception):
    pass


class BadContractPath(Exception):
    pass


class BadContractGroup(Exception):
    pass


class BadVersionError(Exception):
    pass


DeploymentExceptions = (
    botocore.exceptions.ClientError,
    BadActiveContract,
    BadContractGroup,
    BadContractPath,
    BadVersionError,
)

from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json


def refresh_ecs_service(cluster_name_lookup: str):
    session = new_aws_session()
    tf_json = get_terraform_json()
    ecs = session.client("ecs")
    cluster_info = tf_json[cluster_name_lookup]["value"]
    ecs.update_service(**cluster_info, forceNewDeployment=True)

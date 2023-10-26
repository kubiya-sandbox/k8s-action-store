import logging
from typing import List

from . import actionstore as action_store
from .clients import get_batch_client, get_core_api_client
from kubernetes.client import V1Namespace

from pydantic import BaseModel

from .cronjobs import CronjobDisableInput, CronjobsDisableInput, disable_cronjobs, list_enabled_cronjobs_for_namespace
from .deployment import list_deployment, Deployment, DeploymentReplicasInputSingle, DeploymentsReplicasInput, \
    scale_deployments


class NamespaceMeta(BaseModel):
    namespace: str

# Init logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@action_store.kubiya_action()
# Every action should recieve a param object
def list_namespace(params):
    api_client = get_core_api_client()
    api_response = api_client.list_namespace()
    return [item.metadata.name for item in api_response.items]

@action_store.kubiya_action()
def create_namespace(namespace: NamespaceMeta):
    api_client = get_core_api_client()
    namespace_body = V1Namespace(
        metadata={
            "name": namespace.namespace,
        }
    )
    api_response = api_client.create_namespace(body=namespace_body)
    return {"status": "created", "namespace": api_response.metadata.name}

@action_store.kubiya_action()
def delete_namespace(namespace: NamespaceMeta):
    api_client = get_core_api_client()
    api_response = api_client.delete_namespace(name=namespace.namespace)
    return {"status": "deleted", "namespace": namespace.namespace}

@action_store.kubiya_action()
def get_namespace(namespace: NamespaceMeta):
    api_client = get_core_api_client()
    api_response = api_client.read_namespace(name=namespace.namespace)
    return api_response.to_dict()

@action_store.kubiya_action()
def scale_env_to_zero(args):
    logger.info("scale_env_to_zero has started")
    list_deployment_input = Deployment(namespace=args.get("namespace"))
    logging.info("calling list_deployment action")
    deployments = list_deployment(list_deployment_input)
    logging.info("list_deployment action has finished")
    deployments_list = []
    for i, d in enumerate(deployments):
        deployment_input = DeploymentReplicasInputSingle(
            deployment_name=d,
            replicas=0
        )
        deployments_list.append(deployment_input)
    deployments_to_scale_input = DeploymentsReplicasInput(
        namespace=args.get("namespace"),
        inputs=deployments_list,
    )
    logging.info("calling scale_deployments")
    deployment_res = scale_deployments(deployments_to_scale_input)
    if "error" in deployment_res:
        logging.error(deployment_res)
    logging.debug(f"response of scale_deployments is: {deployment_res}")

    logger.info("calling list_enabled_cronjobs_for_namespace")
    enabled_cronjobs = list_enabled_cronjobs_for_namespace({"namespace": args.get("namespace")})
    cronjobs_list = []
    for i, c in enumerate(enabled_cronjobs):
        cronjob_input = CronjobDisableInput(
            namespace=args.get("namespace"),
            cron_name=c
        )
        cronjobs_list.append(cronjob_input)
    disable_cronjobs_input = CronjobsDisableInput(
        namespace=args.get("namespace"),
        crons=cronjobs_list
    )
    cronjobs_res = disable_cronjobs(disable_cronjobs_input)
    if "error" in cronjobs_res:
        logging.error(cronjobs_res)
    logging.debug(f"response of disable_cronjobs is: {cronjobs_res}")
    return {"status": "success", "deployments": deployment_res, "cronjobs": cronjobs_res}
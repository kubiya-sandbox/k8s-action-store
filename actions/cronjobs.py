import logging
from typing import Optional, List

from pydantic import BaseModel

from . import actionstore as action_store
from .clients import get_batch_client

class Namespace(BaseModel):
    name: str

# Init logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@action_store.kubiya_action()
def list_suspended_cronjobs(args):
    api_client = get_batch_client()
    api_response = api_client.list_cron_job_for_all_namespaces()
    suspended_cronjobs = [cj for cj in api_response.items if cj.spec.suspend == True]
    return [item.metadata.name for item in suspended_cronjobs]


@action_store.kubiya_action()
def list_suspended_cronjobs_for_namespace(args: Namespace):
    api_client = get_batch_client()
    api_response = api_client.list_namespaced_cron_job(args.name)
    suspended_cronjobs = [cj for cj in api_response.items if cj.spec.suspend == True]
    return [item.metadata.name for item in suspended_cronjobs]


@action_store.kubiya_action()
def list_disabled_cronjobs_for_all_namespaces(args):
    api_client = get_batch_client()
    api_response = api_client.list_cron_job_for_all_namespaces()
    return [
        item.metadata.name for item in api_response.items if item.spec.schedule == ""
    ]

@action_store.kubiya_action()
def list_disabled_cronjobs_for_namespace(args):
    api_client = get_batch_client()
    namespace = args.get("namespace")
    api_response = api_client.list_namespaced_cron_job(namespace)
    return [
        item.metadata.name for item in api_response.items if item.spec.schedule == ""
    ]

@action_store.kubiya_action()
def list_enabled_cronjobs_for_namespace(args):
    api_client = get_batch_client()
    namespace = args.get("namespace")
    api_response = api_client.list_namespaced_cron_job(namespace)
    return [
        item.metadata.name for item in api_response.items if item.spec.schedule != ""
    ]

@action_store.kubiya_action()
def delete_stuck_cronjob(args):
    api_client = get_batch_client()
    api_response = api_client.list_cron_job_for_all_namespaces()
    stuck_cronjobs = [cj for cj in api_response.items if cj.spec.suspend == True]
    for cronjob in stuck_cronjobs:
        api_client.delete_namespaced_cron_job(
            cronjob.metadata.name, cronjob.metadata.namespace
        )

    return [item.metadata.name for item in stuck_cronjobs]

class CronjobDisableInput(BaseModel):
    namespace: Optional[str] = "default"
    cron_name: Optional[str] = None

@action_store.kubiya_action()
def disable_cronjob(args: CronjobDisableInput):
    try:
        cron_job_name = args.cron_name
        namespace = args.namespace
        api_client = get_batch_client()
        api_response = api_client.patch_namespaced_cron_job(cron_job_name, namespace, {"spec": {"suspend": True}})
        return {"status": "success", "replicas": api_response}
    except api_client.rest.ApiException as e:
        return {"error": e.reason}

@action_store.kubiya_action()
def enable_cronjob(args):
    api_client = get_batch_client()
    cron_job_name = args.get("cron_job_name")
    namespace = args.get("namespace")
    api_client.patch_namespaced_cron_job(
        cron_job_name, namespace, {"spec": {"suspend": False}}
    )
    return "cron job - {} - enabled".format(cron_job_name)

class CronjobsDisableInput(BaseModel):
    namespace: Optional[str] = "default"
    crons: List[CronjobDisableInput]
@action_store.kubiya_action()
def disable_cronjobs(args: CronjobsDisableInput):
    logger.info(f"Scaling {len(args.crons)} deployments")
    res_dict = {}
    for i, _input in enumerate(args.crons):
        logger.info(f"disabling cron job {i+1}/{len(args.crons)} ...")
        disable_cron_input = CronjobDisableInput(
            namespace=args.namespace,
            cron_name=_input.cron_name,
        )
        res = disable_cronjob(disable_cron_input)
        res_dict[_input.cron_name] = res

    success = []
    failed = []
    for cron, res in res_dict.items():
        e = res.get("error")
        if "error" in res:
            failed.append({"cronjob": cron, "namespace": args.namespace, "error": e})
        else:
            success.append({"cronjob": cron, "namespace": args.namespace})

    logger.info("Finished disabling cronjobs")
    if failed:
        return {"success": success, "failed": failed, "error": failed}
    return {"success": success, "failed": failed}


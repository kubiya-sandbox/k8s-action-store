from pydantic import BaseModel
from . import actionstore as action_store
from kubernetes.client.exceptions import ApiException
from .clients import get_apps_client

import logging

# Init logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class CreateDaemonSetInput(BaseModel):
    name: str
    namespace: str
    container_name: str
    container_image: str
    update_strategy_type: str

class ErrorResponse(BaseModel):
    error: str

class DeleteDaemonSetInput(BaseModel):
    name: str
    namespace: str

class ErrorResponse(BaseModel):
    error: str

class GetDaemonSetResponse(BaseModel):
    api_version: str
    kind: str
    metadata: dict
    spec: dict

class UpdateDaemonSetInput(BaseModel):
    name: str
    namespace: str
    container_image: str
    container_name: str
    update_strategy_type: str



@action_store.kubiya_action()
def create_daemonset(data: CreateDaemonSetInput) -> dict:
    api_instance = get_apps_client()

    daemonset_manifest = {
        "apiVersion": "apps/v1",
        "kind": "DaemonSet",
        "metadata": {
            "name": data.name
        },
        "spec": {
            "selector": {
                "matchLabels": {"app": data.name}  # Using the DaemonSet name as a label
            },
            "template": {
                "metadata": {
                    "labels": {"app": data.name}  # Using the DaemonSet name as a label
                },
                "spec": {
                    "containers": [
                        {
                            "name": data.container_name,
                            "image": data.container_image,
                        }
                    ]
                }
            },
            "updateStrategy": {
                "type": data.update_strategy_type
            }
        }
    }

    try:
        api_response = api_instance.create_namespaced_daemon_set(
            body=daemonset_manifest,
            namespace=data.namespace
        )
        return api_response.to_dict()
    except ApiException as e:
        return {"error": str(e)}



@action_store.kubiya_action()
def delete_daemonset(data: DeleteDaemonSetInput) -> dict:
    api_instance = get_apps_client()

    try:
        api_response = api_instance.delete_namespaced_daemon_set(
            name=data.name,
            namespace=data.namespace
        )
        return {"status": api_response.status}
    except ApiException as e:
        return ErrorResponse(error=str(e)).dict()


@action_store.kubiya_action()
def get_daemonset(data: DeleteDaemonSetInput) -> dict:
    api_instance = get_apps_client()

    try:
        api_response = api_instance.read_namespaced_daemon_set(
            name=data.name,
            namespace=data.namespace
        )
        return GetDaemonSetResponse(**api_response.to_dict()).dict()
    except ApiException as e:
        return ErrorResponse(error=str(e)).dict()
    

@action_store.kubiya_action()
def update_daemonset(data: UpdateDaemonSetInput) -> dict:
    api_instance = get_apps_client()

    daemonset_manifest = {
        "apiVersion": "apps/v1",
        "kind": "DaemonSet",
        "metadata": {
            "name": data.name
        },
        "spec": {
            "selector": {
                "matchLabels": {"app": data.name}
            },
            "template": {
                "metadata": {
                    "labels": {"app": data.name}
                },
                "spec": {
                    "containers": [
                        {
                            "name": data.container_name,
                            "image": data.container_image,
                        }
                    ]
                }
            },
            "updateStrategy": {
                "type": data.update_strategy_type
            }
        }
    }

    try:
        api_response = api_instance.patch_namespaced_daemon_set(
            name=data.name,
            namespace=data.namespace,
            body=daemonset_manifest
        )
        return api_response.to_dict()
    except ApiException as e:
        return {"error": str(e)}
from typing import Optional, List
from kubernetes import client, stream
from pydantic import BaseModel

from . import actionstore as action_store
from .clients import get_core_api_client


class NamespaceModel(BaseModel):
    namespace: str


class CommandModel(BaseModel):
    namespace: str
    pod_name: str
    command: List[str]


class DeletePodModel(BaseModel):
    namespace: str
    pod_name: str


class LabelModel(BaseModel):
    namespace: str
    label: str


@action_store.kubiya_action()
def exec_command_in_pod(data: CommandModel) -> str:
    try:
        api_client = get_core_api_client()

        resp = stream.stream(
            api_client.connect_get_namespaced_pod_exec,
            name=data.pod_name,
            namespace=data.namespace,
            command=data.command,
            stderr=True, stdin=True, stdout=True, tty=False
        )

        return resp
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def delete_namespaced_pod(data: DeletePodModel) -> dict:
    try:
        api_client = get_core_api_client()

        resp = api_client.delete_namespaced_pod(
            name=data.pod_name,
            namespace=data.namespace,
            body=client.V1DeleteOptions(),
        )

        return resp.to_dict()
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def list_namespaced_pod(data: NamespaceModel) -> List[dict]:
    try:
        api_client = get_core_api_client()

        resp = api_client.list_namespaced_pod(namespace=data.namespace)

        return [i.to_dict() for i in resp.items]
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def get_pod_logs_by_label(data: LabelModel) -> List[str]:
    try:
        api_client = get_core_api_client()

        label_selector = "controller-uid={}".format(data.label)
        resp = api_client.list_namespaced_pod(
            namespace=data.namespace, 
            label_selector=label_selector
        )

        if resp.items:
            pod_name = resp.items[0].metadata.name
            return api_client.read_namespaced_pod_log(pod_name, data.namespace).split("\n")
        else:
            return ["No pods found"]
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def create_namespaced_pod(data: NamespaceModel) -> dict:
    try:
        api_client = get_core_api_client()

        pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(name=data.namespace),
        )

        resp = api_client.create_namespaced_pod(
            namespace=data.namespace, body=pod
        )

        return resp.to_dict()
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def patch_namespaced_pod(data: NamespaceModel) -> dict:
    try:
        api_client = get_core_api_client()

        resp = api_client.patch_namespaced_pod(
            name=data.namespace, 
            namespace=data.namespace, 
            body={}
        )

        return resp.to_dict()
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def read_namespaced_pod(data: NamespaceModel) -> dict:
    try:
        api_client = get_core_api_client()

        resp = api_client.read_namespaced_pod(
            name=data.namespace, 
            namespace=data.namespace
        )

        return resp.to_dict()
    except client.rest.ApiException as e:
        return {"error": e.reason}


@action_store.kubiya_action()
def list_failed_pods(data: NamespaceModel) -> List[str]:
    try:
        api_client = get_core_api_client()

        field_selector = "status.phase=Failed"
        resp = api_client.list_pod_for_all_namespaces(
            field_selector=field_selector
        )

        return [item.metadata.name for item in resp.items]
    except client.rest.ApiException as e:
        return {"error": e.reason}
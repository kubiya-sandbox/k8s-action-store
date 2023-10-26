from typing import Optional, List
from pydantic import BaseModel
from kubernetes import client

from . import actionstore as action_store
from .clients import get_core_api_client


class Service(BaseModel):
    name: str
    namespace: str
    type: str
    cluster_ip: Optional[str]
    external_ip: Optional[str]
    ports: Optional[List[str]]


@action_store.kubiya_action()
def list_services(namespace: str) -> List[Service]:
    api_client = get_core_api_client()
    api_response = api_client.list_namespaced_service(namespace)
    services = []
    for item in api_response.items:
        service = Service(
            name=item.metadata.name,
            namespace=item.metadata.namespace,
            type=item.spec.type,
            cluster_ip=item.spec.cluster_ip,
            external_ip=item.spec.external_i_ps,
            ports=[f"{port.protocol}/{port.port}" for port in item.spec.ports],
        )
        services.append(service)
    return services


@action_store.kubiya_action()
def get_service(namespace: str, service_name: str) -> Service:
    api_client = get_core_api_client()
    api_response = api_client.read_namespaced_service(service_name, namespace)
    service = Service(
        name=api_response.metadata.name,
        namespace=api_response.metadata.namespace,
        type=api_response.spec.type,
        cluster_ip=api_response.spec.cluster_ip,
        external_ip=api_response.spec.external_i_ps,
        ports=[f"{port.protocol}/{port.port}" for port in api_response.spec.ports],
    )
    return service
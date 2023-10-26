from typing import List

from pydantic import BaseModel

from . import actionstore as s
from .clients import get_batch_client, get_core_api_client, get_apps_client


class HealthRequest(BaseModel):
    pass


class HealthResponse(BaseModel):
    params: bool
    connection: bool
    errors: List[str]


@s.kubiya_action()
def health_check(_: HealthRequest) -> HealthResponse:
    errors = List[str]
    apps = get_apps_client()
    batch = get_batch_client()
    core = get_core_api_client()
    connection = _validate_conn(clients=[core, apps, batch], e=errors)
    return HealthResponse(params=True, connection=connection, errors=errors)


def _validate_conn(clients: List[any], e: List[str]) -> bool:
    valid = True
    for c in clients:
        try:
            valid = valid and c.get_api_resources().items >= 1
        except Exception as e:
            valid = False
            e.append(f"faild to connect to Kubernetes: {str(e)}")

    return valid

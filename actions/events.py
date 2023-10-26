from typing import Optional
from kubernetes import client
from pydantic import BaseModel

from . import actionstore as action_store
from .clients import get_core_api_client

class EventFilter(BaseModel):
    namespace: Optional[str] = None

@action_store.kubiya_action()
def get_events(event_filter: EventFilter):
    """Fetch Kubernetes events"""

    try:
        api_client = get_core_api_client()

        if event_filter.namespace:
            events = api_client.list_namespaced_event(event_filter.namespace)
        else:
            events = api_client.list_event_for_all_namespaces()

        return {"data": [event.to_dict() for event in events.items]}

    except client.rest.ApiException as e:
        return {"error": e.reason}
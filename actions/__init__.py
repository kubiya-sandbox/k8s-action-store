import time
from os import environ
from pprint import pprint

import yaml

# from sh import gcloud
from kubiya import ActionStore, get_secret

from kubernetes import client, config

actionstore = ActionStore("kubernetes", "0.1.0")

# actionstore.uses_secrets(["GKE_SERVICE_ACCOUNT", "GKE_PROJECT", "GKE_CLUSTER_REGION", "GKE_CLUSTER_NAME",])

# GKE_SERVICE_ACCOUNT = actionstore.secrets.get("GKE_SERVICE_ACCOUNT")
# GKE_CLUSTER_REGION = actionstore.secrets.get("GKE_CLUSTER_REGION")
# GKE_CLUSTER_NAME = actionstore.secrets.get("GKE_CLUSTER_NAME")
# GKE_PROJECT = actionstore.secrets.get("GKE_PROJECT")


# initialized = False

# def init():
#     if initialized:
#         return
#     with open("/opt/gcloud-service-account.json", "w") as f:
#         f.write(GKE_SERVICE_ACCOUNT)
#     gcloud("auth", "activate-service-account", "--key-file=/opt/gcloud-service-account.json")
#     gcloud("config", "set", "project", GKE_PROJECT, "--quiet")
#     gcloud("container", "clusters", "get-credentials", GKE_CLUSTER_NAME, "--region", GKE_CLUSTER_REGION)
#     print("initialized...")
#     initialized = True


def login():
    # init()
    config.load_kube_config()
    return client.CoreV1Api()


cli = client.CoreV1Api()  # default api client
apiClient = client.ApiClient()


def get_v1_methods():
    return [
        method
        for method in dir(cli)
        if callable(getattr(cli, method)) and not method.startswith("_")
    ]


def method_wrapper(methodname):
    def wrapper(*args, **kwargs):
        cli = login()
        func = getattr(cli, methodname)
        return apiClient.sanitize_for_serialization(func(*args, **kwargs))

    return wrapper


def register_methods(actions):
    for methodname in actions:
        actionstore.register_action(methodname, method_wrapper(methodname))


# if __name__ == "__main__":
#     cli = login()
#     pprint(cli.list_namespace())
# else:
#     register_methods(get_v1_methods())

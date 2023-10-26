import kubernetes
from kubernetes import config

config.load_incluster_config()
# Create a custom configuration object to disable SSL verification
client_config = kubernetes.client.Configuration()

# Create a custom configuration object with the correct host name
client_config.host = "https://kubernetes.default.svc:443"

# Load the service account token and create the API client
client_config.api_key = {
    "authorization": "Bearer "
    + open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()
}
client_config.ssl_ca_cert = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"


def get_batch_client():
    return kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(client_config))


def get_apps_client():
    return kubernetes.client.AppsV1Api(kubernetes.client.ApiClient(client_config))


def get_core_api_client():
    return kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(client_config))

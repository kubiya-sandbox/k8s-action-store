import datetime
import logging
import os
import time
from datetime import timedelta
from typing import Dict, Optional

from pydantic import BaseModel

from kubernetes.client import (
    V1Container,
    V1EnvVar,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
)
from kubernetes.client.rest import ApiException

from . import actionstore as action_store
from .clients import get_batch_client, get_core_api_client

logging.basicConfig(level=logging.INFO)


class Job(BaseModel):
    name: str
    image: str
    command: Optional[str]
    resources: Optional[dict] = None
    kubernetes_client_retry_attempts: int = 44
    kubernetes_client_timeout: int = 55
    job_name: str = "example-job"
    namespace: str = "default"
    image: str = "busybox:latest"
    container_name: str = "sample-job"
    env_vars: Optional[Dict[str, str]] = None
    app_label: str = "example-job"
    restart_policy: str = "Never"

class JobMeta(BaseModel):
    name: str
    namespace: str = "default"

class JobCompletionMeta(JobMeta):
    timeout: int = 300

class JobScaleInput(JobMeta):
    parallelism: int
    completions: int

class JobStatusOutput(BaseModel):
    active: Optional[int]
    succeeded: Optional[int]
    failed: Optional[int]

class Namespace(BaseModel):
    namespace: str = "default"

@action_store.kubiya_action()
def scale_job(params: JobScaleInput):
    api_client = get_batch_client()
    api_response = api_client.read_namespaced_job(params.name, params.namespace)
    api_response.spec.parallelism = params.parallelism
    api_response.spec.completions = params.completions
    api_response = api_client.patch_namespaced_job(params.name, params.namespace, api_response)
    return api_response

@action_store.kubiya_action()
def get_job_status(job: JobMeta) -> JobStatusOutput:
    api_client = get_batch_client()
    api_response = api_client.read_namespaced_job(job.name, job.namespace)
    status = api_response.status
    return JobStatusOutput(active=status.active, succeeded=status.succeeded, failed=status.failed)

@action_store.kubiya_action()
def get_job_events(job: JobMeta):
    api_client = get_core_api_client()
    api_response = api_client.list_namespaced_event(job.namespace, field_selector=f"involvedObject.kind=Job,involvedObject.name={job.name}")
    return [event.message for event in api_response.items]


@action_store.kubiya_action()
def suspend_job(job: JobMeta):
    api_client = get_batch_client()
    api_response = api_client.read_namespaced_job(job.name, job.namespace)
    api_response.spec.suspend = True
    api_response = api_client.patch_namespaced_job(job.name, job.namespace, api_response)
    return api_response

@action_store.kubiya_action()
def resume_job(job: JobMeta):
    api_client = get_batch_client()
    api_response = api_client.read_namespaced_job(job.name, job.namespace)
    api_response.spec.suspend = False
    api_response = api_client.patch_namespaced_job(job.name, job.namespace, api_response)
    return api_response


@action_store.kubiya_action()
def wait_for_job_completion(job: JobCompletionMeta):
    api_client = get_batch_client()
    start_time = time.time()
    while time.time() - start_time < job.timeout:
        api_response = api_client.read_namespaced_job(job.name, job.namespace)
        if api_response.status.succeeded is not None:
            return {"status": "completed"}
        time.sleep(5)
    return {"status": "timeout"}

@action_store.kubiya_action()
def create_namespaced_job(job: Job):
    start_time = datetime.datetime.now()
    timeout_time = start_time + timedelta(seconds=job.kubernetes_client_timeout)
    api_client = get_batch_client()

    logging.info("Attempting to create namespaced job")
    if not job.env_vars:
        job.env_vars = {"EXAMPLE_ENV_VAR": "example-value"}
    container = V1Container(
        name=job.container_name,
        image=job.image,
        env=[V1EnvVar(name=k, value=v) for k, v in job.env_vars.items()],
    )

    job_spec = V1JobSpec(
        template=V1PodTemplateSpec(
            metadata=V1ObjectMeta(labels={"app": job.app_label}),
            spec=V1PodSpec(
                containers=[container],
                # TODO:: Support ability to pass dynamic commands
                restart_policy=job.restart_policy,
            ),
        ),
        backoff_limit=4,
    )

    # Create the job
    new_job = V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=V1ObjectMeta(name=job.name),
        spec=job_spec,
    )
    try:
        api_response = api_client.create_namespaced_job(
            namespace=job.namespace, body=new_job
        )
        logging.info(f"Job created. response='{str(api_response)}")
    except ApiException as e:
        # create a meaningful error message
        raise ApiException(
            f"Exception when calling BatchV1Api->create_namespaced_job: {e.body}"
        )
        # In case the job succeeded to start, get its logs
    try:
        # Wait for the job to launch a pod
        while datetime.datetime.now() < timeout_time:
            logging.info("Waiting for job to start")
            api_response = api_client.read_namespaced_job(job.name, job.namespace)
            # Get the pod name from the job
            logging.info(f"current status: {api_response}")

            if api_response.status.active not in [None, 0]:
                return {"status": api_response.status.active}
            time.sleep(1.5)

    except ApiException as e:
        raise ApiException(
            f"Exception when calling BatchV1Api->read_namespaced_job: {e.body}"
        )

@action_store.kubiya_action()
def delete_namespaced_job(job: JobMeta):
    api_client = get_batch_client()
    try:
        api_response = api_client.delete_namespaced_job(
            job.name, job.namespace, propagation_policy="Background"
        )
        logging.info(f"Job deleted. response='{str(api_response)}")
    except ApiException as e:
        # create a meaningful error message
        raise ApiException(
            f"Exception when calling BatchV1Api->delete_namespaced_job: {e.body}"
        )

@action_store.kubiya_action()
def list_namespaced_jobs(namespace: Namespace):
    api_client = get_batch_client()
    jobs = []
    try:
        api_response = api_client.list_namespaced_job(namespace.namespace)
        logging.info(f"Job listed. response='{str(api_response)}")
        for item in api_response.items:
            jobs.append(item.metadata.name)
        return jobs
    except ApiException as e:
        # create a meaningful error message
        return {"error": f"Exception when calling BatchV1Api->list_namespaced_job: {e.body}"}

@action_store.kubiya_action()
def get_namespaced_job_logs(job: JobMeta):
    try:
        core_api_client = get_core_api_client()
        while True:
            label_selector = f"job-name={job.name}"
            pod_list = core_api_client.list_namespaced_pod(
                job.namespace, label_selector=label_selector
            )
            if len(pod_list.items) > 0:
                break
            time.sleep(1)
        pod_name = pod_list.items[0].metadata.name
        logging.info(f"Found pod:{pod_name}")

        while True:
            pod = core_api_client.read_namespaced_pod(pod_name, job.namespace)
            if pod.status.phase != "Pending":
                logs = core_api_client.read_namespaced_pod_log(pod_name, job.namespace)
                return logs.splitlines()
            time.sleep(1)
    except Exception as e:
        raise Exception(
            f"Exception when calling BatchV1Api->create_namespaced_job: {e}"
        )
    
@action_store.kubiya_action()
def get_job_controller_uid(job: JobMeta):
    api_client = get_batch_client()
    api_response = api_client.read_namespaced_job(job.name, job.namespace)
    return api_response.metadata.labels['controller-uid']

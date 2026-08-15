#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
General Kubernetes API Client Example
Can be used to perform various Kubernetes API operations
"""
import logging
import os

import yaml
from dotenv import load_dotenv
from kubernetes import client, config
from kubernetes.client import V1DeleteOptions
from kubernetes.client.rest import ApiException


class KubernetesApiClient:
    """Kubernetes API Client Wrapper Class"""

    def __init__(self, kubeconfig_path=None, context=None, in_cluster=False):
        """
        Initialize Kubernetes API Client

        Args:
            kubeconfig_path: kubeconfig file path, defaults to None which uses ~/.kube/config
            context: kubeconfig context name to use
            in_cluster: whether running inside a cluster, if True use service account configuration
        """
        try:
            # Use absolute path relative to the script file for KUBECONFIG_PATH
            load_dotenv()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, "kubeconfig")
            kubeconfig_path = kubeconfig_path or os.getenv("KUBECONFIG_PATH") or script_path
            if in_cluster:
                config.load_incluster_config()
            else:
                config.load_kube_config(
                    config_file=kubeconfig_path,
                    context=context
                )

            # Initialize various API clients
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.custom_objects = client.CustomObjectsApi()

            logging.info("Kubernetes API client initialized successfully")
        except Exception as e:
            logging.info(f"Failed to initialize Kubernetes API client: {e}")
            raise

    # ===================== Pod Operations =====================

    def get_pod(self, name, namespace="default"):
        """
        Get a specific Pod in the given namespace
        Equivalent to: GET /api/v1/namespaces/{namespace}/pods/{name}
        """
        try:
            return self.core_v1.read_namespaced_pod(
                name=name,
                namespace=namespace
            )
        except ApiException as e:
            logging.warning(f"Failed to get Pod {namespace}/{name}: {e}")
            return None

    def list_pods(self, namespace="default", label_selector=None, field_selector=None):
        """
        List all Pods in the given namespace
        Equivalent to: GET /api/v1/namespaces/{namespace}/pods
        """
        try:
            return self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector,
                field_selector=field_selector
            )
        except ApiException as e:
            logging.warning(f"Failed to list Pods in namespace {namespace}: {e}")
            return None

    def list_pods_all_namespaces(self, label_selector=None, field_selector=None):
        """
        List Pods across all namespaces
        Equivalent to: GET /api/v1/pods
        """
        try:
            return self.core_v1.list_pod_for_all_namespaces(
                label_selector=label_selector,
                field_selector=field_selector
            )
        except ApiException as e:
            logging.warning(f"Failed to list Pods across all namespaces: {e}")
            return None

    def create_pod(self, pod_manifest, namespace="default"):
        """
        Create a Pod
        Equivalent to: POST /api/v1/namespaces/{namespace}/pods

        Args:
            pod_manifest: Pod resource definition, can be dict or V1Pod object
            namespace: Namespace where the Pod will be created

        Returns:
            V1Pod: The created Pod object on success
            None: On failure
        """
        try:
            # If input is a dictionary, use it directly
            if isinstance(pod_manifest, dict):
                # Using dictionary definition
                return self.core_v1.create_namespaced_pod(
                    namespace=namespace,
                    body=pod_manifest
                )
            else:
                # Using V1Pod object directly
                return self.core_v1.create_namespaced_pod(
                    namespace=namespace,
                    body=pod_manifest
                )
        except ApiException as e:
            logging.warning(f"Failed to create Pod: {e}")
            return None

    def create_pod_from_yaml(self, yaml_file=None, namespace=None, pod_name=None):
        """
        Create a Pod from YAML file

        Args:
            yaml_file: YAML file path
            namespace: Namespace where the Pod will be created
            pod_name: Override the Pod name in the YAML

        Returns:
            V1Pod: The created Pod object on success
            None: On failure
        """
        try:
            load_dotenv()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pod_path = os.path.join(script_dir, "pod.yaml")
            yaml_file = yaml_file or os.getenv("POD_YAML_PATH") or pod_path
            namespace = namespace or os.getenv("POD_NAMESPACE") or "default"
            with open(yaml_file, 'r') as f:
                pod_manifest = yaml.safe_load(f)
            # Update Pod name if provided
            if pod_name:
                if 'metadata' in pod_manifest:
                    pod_manifest['metadata']['name'] = pod_name
                    if 'labels' in pod_manifest['metadata']:
                        pod_manifest['metadata']['labels']['name'] = pod_name
                if 'spec' in pod_manifest and 'containers' in pod_manifest['spec'] and pod_manifest['spec'][
                    'containers']:
                    pod_manifest['spec']['containers'][0]['name'] = pod_name

            return self.create_pod(pod_manifest, namespace)
        except Exception as e:
            logging.info(f"Failed to create Pod from YAML file: {e}")
            return None

    def delete_pod(self, name, namespace="default", grace_period_seconds=30):
        """
        Delete a Pod
        Equivalent to: DELETE /api/v1/namespaces/{namespace}/pods/{name}

        Args:
            name: Pod name
            namespace: Namespace where the Pod is located
            grace_period_seconds: Grace period in seconds

        Returns:
            V1Status: Status object on successful deletion
            None: On failure
        """
        try:
            return self.core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
                body=V1DeleteOptions(
                    grace_period_seconds=grace_period_seconds,
                    propagation_policy="Background"
                )
            )
        except ApiException as e:
            logging.warning(f"Failed to delete Pod {namespace}/{name}: {e}")
            return None

    def update_pod(self, name, pod_manifest, namespace="default"):
        """
        Update a Pod
        Equivalent to: PUT /api/v1/namespaces/{namespace}/pods/{name}

        Args:
            name: Pod name
            pod_manifest: Pod resource definition, can be dict or V1Pod object
            namespace: Namespace where the Pod is located

        Returns:
            V1Pod: The updated Pod object on success
            None: On failure
        """
        try:
            # If input is a dictionary, ensure name and namespace fields
            if isinstance(pod_manifest, dict):
                if 'metadata' not in pod_manifest:
                    pod_manifest['metadata'] = {}
                pod_manifest['metadata']['name'] = name
                pod_manifest['metadata']['namespace'] = namespace

                return self.core_v1.replace_namespaced_pod(
                    name=name,
                    namespace=namespace,
                    body=pod_manifest
                )
            else:
                # Ensure V1Pod object has correct name and namespace
                pod_manifest.metadata.name = name
                pod_manifest.metadata.namespace = namespace

                return self.core_v1.replace_namespaced_pod(
                    name=name,
                    namespace=namespace,
                    body=pod_manifest
                )
        except ApiException as e:
            logging.warning(f"Failed to update Pod {namespace}/{name}: {e}")
            return None

    def patch_pod(self, name, patch_data, namespace="default"):
        """
        Partially update a Pod
        Equivalent to: PATCH /api/v1/namespaces/{namespace}/pods/{name}

        Args:
            name: Pod name
            patch_data: Data to update, in dictionary format
            namespace: Namespace where the Pod is located

        Returns:
            V1Pod: The updated Pod object on success
            None: On failure
        """
        try:
            return self.core_v1.patch_namespaced_pod(
                name=name,
                namespace=namespace,
                body=patch_data
            )
        except ApiException as e:
            logging.warning(f"Failed to patch Pod {namespace}/{name}: {e}")
            return None

    def get_pod_info(self, name, namespace="default"):
        """
        Get basic information about a Pod

        Args:
            name: Pod name
            namespace: Namespace where the Pod is located

        Returns:
            dict: Dictionary containing basic Pod information including status, IP, start time, etc.
            None: On failure
        """
        try:
            pod = self.get_pod(name, namespace)
            if not pod:
                return None

            # Format start time for readability
            start_time = None
            if pod.status.start_time:
                # Convert time to readable format (ISO format: YYYY-MM-DD HH:MM:SS)
                start_time_obj = pod.status.start_time.replace(tzinfo=None)
                start_time = start_time_obj.strftime('%Y-%m-%d %H:%M:%S')

            pod_info = {
                "pod_name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,  # Pending, Running, Succeeded, Failed, Unknown
                "pod_ip": pod.status.pod_ip,
                "host_ip": pod.status.host_ip,
                "start_time": start_time,
                "node_name": pod.spec.node_name if hasattr(pod.spec, "node_name") else None
            }

            return pod_info
        except Exception as e:
            logging.warning(f"Failed to get Pod information for {namespace}/{name}: {e}")
            return None

    # ===================== Deployment Operations =====================

    def get_deployment(self, name, namespace="default"):
        """
        Get a specific Deployment
        Equivalent to: GET /apis/apps/v1/namespaces/{namespace}/deployments/{name}
        """
        try:
            return self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
        except ApiException as e:
            logging.warning(f"Failed to get Deployment {namespace}/{name}: {e}")
            return None

    def list_deployments(self, namespace="default", label_selector=None):
        """
        List all Deployments in the given namespace
        Equivalent to: GET /apis/apps/v1/namespaces/{namespace}/deployments
        """
        try:
            return self.apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=label_selector
            )
        except ApiException as e:
            logging.warning(f"Failed to list Deployments in namespace {namespace}: {e}")
            return None

    # ===================== Service Operations =====================

    def get_service(self, name, namespace="default"):
        """
        Get a specific Service
        Equivalent to: GET /api/v1/namespaces/{namespace}/services/{name}
        """
        try:
            return self.core_v1.read_namespaced_service(
                name=name,
                namespace=namespace
            )
        except ApiException as e:
            logging.warning(f"Failed to get Service {namespace}/{name}: {e}")
            return None

    def list_services(self, namespace="default", label_selector=None):
        """
        List all Services in the given namespace
        Equivalent to: GET /api/v1/namespaces/{namespace}/services
        """
        try:
            return self.core_v1.list_namespaced_service(
                namespace=namespace,
                label_selector=label_selector
            )
        except ApiException as e:
            logging.warning(f"Failed to list Services in namespace {namespace}: {e}")
            return None

    def create_service(self, service_manifest, namespace="default"):
        """
        Create a Service
        Equivalent to: POST /api/v1/namespaces/{namespace}/services

        Args:
            service_manifest: Service resource definition, can be dict or V1Service object
            namespace: Namespace where the Service will be created

        Returns:
            V1Service: The created Service object on success
            None: On failure
        """
        try:
            # If input is a dictionary, use it directly
            if isinstance(service_manifest, dict):
                # Using dictionary definition
                return self.core_v1.create_namespaced_service(
                    namespace=namespace,
                    body=service_manifest
                )
            else:
                # Using V1Service object directly
                return self.core_v1.create_namespaced_service(
                    namespace=namespace,
                    body=service_manifest
                )
        except ApiException as e:
            logging.warning(f"Failed to create Service: {e}")
            return None

    def create_service_from_yaml(self, yaml_file=None, namespace=None, service_name=None, selector_name=None):
        """
        Create a Service from YAML file

        Args:
            yaml_file: YAML file path
            namespace: Namespace where the Service will be created
            service_name: Override the Service name in the YAML
            selector_name: Override the selector name for pod targeting

        Returns:
            V1Service: The created Service object on success
            None: On failure
        """
        try:
            load_dotenv()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            service_path = os.path.join(script_dir, "service.yaml")
            yaml_file = yaml_file or os.getenv("SERVICE_YAML_PATH") or service_path
            namespace = namespace or os.getenv("SERVICE_NAMESPACE") or "default"
            with open(yaml_file, 'r') as f:
                service_manifest = yaml.safe_load(f)

            # Update Service name if provided
            if service_name:
                if 'metadata' in service_manifest:
                    service_manifest['metadata']['name'] = service_name
                    # Update app label if present
                    if 'labels' in service_manifest['metadata']:
                        service_manifest['metadata']['labels']['app'] = service_name

            # Update selector if provided
            if selector_name:
                if 'spec' in service_manifest and 'selector' in service_manifest['spec']:
                    service_manifest['spec']['selector']['name'] = selector_name

            return self.create_service(service_manifest, namespace)
        except Exception as e:
            logging.info(f"Failed to create Service from YAML file: {e}")
            return None

    def update_service(self, name, service_manifest, namespace="default"):
        """
        Update a Service
        Equivalent to: PUT /api/v1/namespaces/{namespace}/services/{name}

        Args:
            name: Service name
            service_manifest: Service resource definition, can be dict or V1Service object
            namespace: Namespace where the Service is located

        Returns:
            V1Service: The updated Service object on success
            None: On failure
        """
        try:
            # If input is a dictionary, ensure name and namespace fields
            if isinstance(service_manifest, dict):
                if 'metadata' not in service_manifest:
                    service_manifest['metadata'] = {}
                service_manifest['metadata']['name'] = name
                service_manifest['metadata']['namespace'] = namespace

                return self.core_v1.replace_namespaced_service(
                    name=name,
                    namespace=namespace,
                    body=service_manifest
                )
            else:
                # Ensure V1Service object has correct name and namespace
                service_manifest.metadata.name = name
                service_manifest.metadata.namespace = namespace

                return self.core_v1.replace_namespaced_service(
                    name=name,
                    namespace=namespace,
                    body=service_manifest
                )
        except ApiException as e:
            logging.warning(f"Failed to update Service {namespace}/{name}: {e}")
            return None

    def patch_service(self, name, patch_data, namespace="default"):
        """
        Partially update a Service
        Equivalent to: PATCH /api/v1/namespaces/{namespace}/services/{name}

        Args:
            name: Service name
            patch_data: Data to update, in dictionary format
            namespace: Namespace where the Service is located

        Returns:
            V1Service: The updated Service object on success
            None: On failure
        """
        try:
            return self.core_v1.patch_namespaced_service(
                name=name,
                namespace=namespace,
                body=patch_data
            )
        except ApiException as e:
            logging.warning(f"Failed to patch Service {namespace}/{name}: {e}")
            return None

    def delete_service(self, name, namespace="default"):
        """
        Delete a Service
        Equivalent to: DELETE /api/v1/namespaces/{namespace}/services/{name}

        Args:
            name: Service name
            namespace: Namespace where the Service is located

        Returns:
            V1Status: Status object on successful deletion
            None: On failure
        """
        try:
            return self.core_v1.delete_namespaced_service(
                name=name,
                namespace=namespace
            )
        except ApiException as e:
            logging.warning(f"Failed to delete Service {namespace}/{name}: {e}")
            return None

    def get_service_info(self, name, namespace="default"):
        """
        Get basic information about a Service

        Args:
            name: Service name
            namespace: Namespace where the Service is located

        Returns:
            dict: Dictionary containing basic Service information including type, IP, ports, etc.
            None: On failure
        """
        try:
            service = self.get_service(name, namespace)
            if not service:
                return None

            # Format creation time for readability
            creation_time = None
            if service.metadata.creation_timestamp:
                creation_time_obj = service.metadata.creation_timestamp.replace(tzinfo=None)
                creation_time = creation_time_obj.strftime('%Y-%m-%d %H:%M:%S')

            # Simplify port information
            ports_info = []
            if service.spec.ports:
                for port in service.spec.ports:
                    port_info = {
                        "port": port.port,
                        "target_port": port.target_port,
                        "protocol": port.protocol
                    }

                    # Add node port if present for NodePort type
                    if hasattr(port, "node_port") and port.node_port:
                        port_info["node_port"] = port.node_port

                    ports_info.append(port_info)

            service_info = {
                "service_name": service.metadata.name,
                "namespace": service.metadata.namespace,
                "type": service.spec.type,  # ClusterIP, NodePort, LoadBalancer, ExternalName
                "cluster_ip": service.spec.cluster_ip,
                "creation_time": creation_time,
                "ports": ports_info,
                "selector": service.spec.selector,
                "host": ''  # Default to use cluster_ip as host
            }

            # Add external IP information for LoadBalancer type
            if service.spec.type == "LoadBalancer" and hasattr(service.status,
                                                               "load_balancer") and service.status.load_balancer:
                external_ips = []
                if hasattr(service.status.load_balancer, "ingress") and service.status.load_balancer.ingress:
                    for ingress in service.status.load_balancer.ingress:
                        if hasattr(ingress, "ip") and ingress.ip:
                            external_ips.append(ingress.ip)
                        elif hasattr(ingress, "hostname") and ingress.hostname:
                            external_ips.append(ingress.hostname)

                    # If there are external IPs or hostnames, use the first one as the host field
                    if external_ips:
                        service_info["host"] = external_ips[0]

                service_info["external_ips"] = external_ips

            # Add external name for ExternalName type
            if service.spec.type == "ExternalName" and hasattr(service.spec, "external_name"):
                service_info["external_name"] = service.spec.external_name
                service_info["host"] = service.spec.external_name  # For ExternalName type, use external_name as host

            return service_info
        except Exception as e:
            print(f"Failed to get Service information for {namespace}/{name}: {e}")
            return None

    # ===================== Namespace Operations =====================

    def get_namespace(self, name):
        """
        Get a specific namespace
        Equivalent to: GET /api/v1/namespaces/{name}
        """
        try:
            return self.core_v1.read_namespace(name=name)
        except ApiException as e:
            logging.warning(f"Failed to get namespace {name}: {e}")
            return None

    def list_namespaces(self, label_selector=None):
        """
        List all namespaces
        Equivalent to: GET /api/v1/namespaces
        """
        try:
            return self.core_v1.list_namespace(label_selector=label_selector)
        except ApiException as e:
            logging.warning(f"Failed to list namespaces: {e}")
            return None

    # ===================== Custom Resource (CRD) Operations =====================

    def get_custom_resource(self, group, version, plural, name, namespace=None):
        """
        Get a custom resource

        For namespaced resources:
        GET /apis/{group}/{version}/namespaces/{namespace}/{plural}/{name}

        For cluster-scoped resources:
        GET /apis/{group}/{version}/{plural}/{name}
        """
        try:
            if namespace:
                return self.custom_objects.get_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    name=name
                )
            else:
                return self.custom_objects.get_cluster_custom_object(
                    group=group,
                    version=version,
                    plural=plural,
                    name=name
                )
        except ApiException as e:
            resource_path = f"{namespace}/{name}" if namespace else name
            logging.warning(f"Failed to get custom resource {group}/{version}/{plural}/{resource_path}: {e}")
            return None


if __name__ == "__main__":
    client = KubernetesApiClient("./kubeconfig")
    # result = client.get_pod("mcp-openapi-node-2", namespace="default")
    # print(result)
    #result = client.create_pod_from_yaml("./pod.yaml")

    # result = client.get_pod_info("mcp-openapi-node-5", namespace="default")
    # print(result)
    result = client.get_service_info("mcp-openapi-service-1", namespace="default")
    print(result)

    # result = client.create_pod_from_yaml("./pod.yaml")
    # print(result)

    # result = client.create_service_from_yaml("./service.yaml")
    # print(result)

    # result = client.delete_pod("mcp-openapi-node-1")
    # print(result)

    # result = client.delete_service("mcp-openapi-service-2")
    # print(result)


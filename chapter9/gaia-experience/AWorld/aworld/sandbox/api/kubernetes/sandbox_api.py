import logging
import time
import datetime
import random
import string
from typing import Dict, List, Any, Optional

from aworld.sandbox.api.base_sandbox_api import BaseSandboxApi
from aworld.sandbox.env_client.kubernetes.client import KubernetesApiClient
from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxK8sResponse
from aworld.sandbox.run.mcp_servers import McpServers


class KubernetesSandboxApi(BaseSandboxApi):
    """
    API implementation for Kubernetes sandbox operations.
    """
    
    @classmethod
    def _create_sandbox(
        cls,
        env_type: int,
        env_config: Any,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
    ) -> SandboxK8sResponse:
        """
        Create a Kubernetes sandbox based on the reference implementation.
        """
        # Initialize these variables outside the try block to avoid accessing undefined variables in exception handling
        client = None
        pod_name = None
        service_name = None

        try:
            # Generate current date and time as prefix, format is yymmddHHMMSS
            date_prefix = datetime.datetime.now().strftime("%y%m%d%H%M%S")
            random_str = cls.generate_random_string()
            pod_name = f"pod-{date_prefix}-{random_str}"
            service_name = f"service-{date_prefix}-{random_str}"
            logging.info(f"Generated pod_name: {pod_name}")
            logging.info(f"Generated service_name: {service_name}")

            client = KubernetesApiClient()

            pod_result = client.create_pod_from_yaml(pod_name=pod_name)
            if not pod_result:
                return None
                
            max_attempts = 30
            attempts = 0
            wait_seconds = 2
            pod_ready = False
            pod_info = None
            
            while attempts < max_attempts:
                pod_info = client.get_pod_info(pod_name)
                pod_ready = pod_info and pod_info.get("status") == SandboxStatus.RUNNING
                if pod_ready:
                    break
                attempts += 1
                if attempts < max_attempts:
                    logging.info(f"Waiting for Pod to be ready, attempt {attempts}/{max_attempts}")
                    time.sleep(wait_seconds)
                    
            if not pod_ready:
                logging.warning("Timed out waiting for Pod and Service to be ready")
                client.delete_pod(pod_name)
                return None

            service_result = client.create_service_from_yaml(service_name=service_name, selector_name=pod_name)
            if not service_result:
                client.delete_pod(pod_name)
                return None

            max_attempts = 30
            attempts = 0
            wait_seconds = 2
            service_ready = False
            service_info = None
            
            while attempts < max_attempts:
                service_info = client.get_service_info(service_name)
                if service_info and ('LoadBalancer' == service_info.get("type") and service_info.get('host')):
                    service_ready = True
                elif service_info and 'ClusterIP' == service_info.get("type"):
                    service_ready = True
                if service_ready:
                    time.sleep(wait_seconds)
                    break
                attempts += 1
                if attempts < max_attempts:
                    logging.info(f"Waiting for Service to be ready, attempt {attempts}/{max_attempts}")
                    time.sleep(wait_seconds)
                    
            if not service_ready:
                client.delete_pod(pod_name)
                client.delete_service(service_name)
                return None

            if pod_ready and service_ready:
                if mcp_servers:
                    try:
                        metadata = {
                            "pod_name": pod_name,
                            "service_name": service_name,
                            "status": pod_info.get("status"),
                            "cluster_ip": service_info.get("cluster_ip"),
                            "host": service_info.get("host"),
                        }
                        
                        response = cls._get_mcp_configs(
                            mcp_servers=mcp_servers,
                            mcp_config=mcp_config,
                            metadata=metadata,
                            env_type=SandboxEnvType.K8S
                        )
                        
                        if response:
                            mcp_config = response
                    except Exception as e:
                        logging.warning(f"Failed to get mcp configs: {e}")

            return SandboxK8sResponse(
                pod_name=pod_name,
                service_name=service_name,
                status=pod_info.get("status"),
                cluster_ip=service_info.get("cluster_ip"),
                host=service_info.get("host"),
                mcp_config=mcp_config,
                env_type=SandboxEnvType.K8S,
            )

        except Exception as e:
            logging.info(f"Failed to create Sandbox by k8s: {e}")
            # Only attempt to delete resources if client has been initialized
            if client:
                if pod_name:
                    client.delete_pod(pod_name)
                if service_name:
                    client.delete_service(service_name)
            return None
    
    @classmethod
    def generate_random_string(cls, length=6):
        """
        Generate a random string of specified length.
        """
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    @classmethod
    def _get_mcp_configs(
        cls,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> Any:
        """
        Get MCP configurations for the sandbox.
        """
        try:
            if not metadata or (
                    not metadata.get("cluster_ip") and not metadata.get("host")):
                return mcp_config
            host = metadata.get("host") or metadata.get("cluster_ip")

            if not mcp_servers:
                return None
            if not mcp_config or mcp_config.get("mcpServers") is None:
                mcp_config = {
                    "mcpServers": {}
                }
            _mcp_servers = mcp_config.get("mcpServers")

            for server in mcp_servers:
                if server not in _mcp_servers:
                    _mcp_servers[server] = {
                        "type": "api",
                        "url": f"http://{host}:80/{server}"
                    }

            return mcp_config
        except Exception as e:
            logging.warning(f"Failed to get_mcp_configs_from_k8s: {e}")
            return None
    
    @classmethod
    async def _remove_sandbox(
        cls,
        sandbox_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> bool:
        """
        Remove the Kubernetes sandbox and clean up resources.
        """
        try:
            if not sandbox_id or not metadata:
                logging.warning(f"sandbox_id={sandbox_id} or metadata={metadata} is None")
                return False

            pod_name = metadata.get("pod_name")
            service_name = metadata.get("service_name")
            
            if not pod_name or not service_name:
                logging.warning(f"pod_name={pod_name} or service_name={service_name} is None")
                return False
                
            client = KubernetesApiClient()
            client.delete_pod(pod_name)
            client.delete_service(service_name)
            return True
            
        except Exception as e:
            logging.warning(f"Failed to remove Sandbox: {e}")
            return False 
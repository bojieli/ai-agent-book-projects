import os

debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
container_server_port = int(os.getenv("CONTAINER_SERVER_PORT", "9000"))

docker_registry_url = os.getenv("DOCKER_REGISTRY_URL")
docker_registry_user_name = os.getenv("DOCKER_REGISTRY_USER_NAME")
docker_registry_password = os.getenv("DOCKER_REGISTRY_PASSWORD")

gateway_server_addr = os.getenv("GATEWAY_SERVER_ADDR", "http://mcp-gateway:8000")

mcp_server_image_id = os.getenv(
    "VIRTUALPC_MCP_SERVER_IMAGE_ID",
    "aworld-registry-registry-vpc.ap-southeast-1.cr.aliyuncs.com/aworld/mcp-server",
)

docker_mode = os.getenv("DOCKER_MODE", "dind")

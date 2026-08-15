import logging
import traceback
from fastapi import Request
import jwt

from ..utils.common_utils import get_remote_addr

from ..configs import token_secret

logger = logging.getLogger(__name__)


def check_auth(request: Request) -> bool:
    payload = get_auth_payload(dict(request.headers))
    logger.info(
        f"Gateway auth: remote.addr={get_remote_addr(request)}, payload={payload}"
    )
    return payload is not None


def get_auth_payload(headers: dict) -> str | None:
    """Check if the request is authorized"""
    try:
        token = headers.get("Authorization")
        if not token:
            return None

        token = token[len("Bearer ") :]
        if not token:
            return None
        payload = decode_token(token)
        return payload
    except Exception as e:
        logger.error(
            f"Failed to check auth, remote.addr={get_remote_addr(request)}, request.headers={request.headers} \n{traceback.format_exc()}"
        )
        return None


def decode_token(token: str) -> str:
    """Decode the token"""
    payload = jwt.decode(token, token_secret, algorithms=["HS256"])
    return payload

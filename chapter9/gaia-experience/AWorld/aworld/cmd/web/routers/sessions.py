import logging
from typing import List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from aworld.cmd.data_model import SessionModel
from aworld.cmd.web.utils.users import get_user_id_from_jwt

logger = logging.getLogger(__name__)

router = APIRouter()

prefix = "/api/session"


@router.get("/list")
async def list_sessions(
    request: Request,
    user_id: str = Depends(get_user_id_from_jwt),
) -> List[SessionModel]:
    return await request.app.state.agent_server.get_session_service().list_sessions(
        user_id
    )


class CommonResponse(BaseModel):
    code: int = Field(..., description="The code")
    message: str = Field(..., description="The message")

    @staticmethod
    def success(message: str = "success"):
        return CommonResponse(code=0, message=message)

    @staticmethod
    def error(message: str):
        return CommonResponse(code=1, message=message)


class DeleteSessionRequest(BaseModel):
    session_id: str = Field(..., description="The session id")


@router.post("/delete")
async def delete_session(
    request: DeleteSessionRequest, user_id: str = Depends(get_user_id_from_jwt)
) -> CommonResponse:
    try:
        await request.app.state.agent_server.get_session_service().delete_session(
            user_id, request.session_id
        )
        return CommonResponse.success()
    except Exception as e:
        return CommonResponse.error(str(e))

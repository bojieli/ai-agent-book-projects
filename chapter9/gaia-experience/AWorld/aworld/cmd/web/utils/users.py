from fastapi import Request

def get_user_id_from_jwt(request: Request) -> str:
    return f"default_user_001"

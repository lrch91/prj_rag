"""认证相关 Pydantic Schema"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    username: str
    full_name: str | None
    role: str

    model_config = {"from_attributes": True}

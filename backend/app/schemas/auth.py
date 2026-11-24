from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.auth import UserRole


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[UserRole] = None
    organization_name: Optional[str] = Field(None, min_length=2, max_length=255)
    organization_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    organization: Optional[OrganizationResponse] = None
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None

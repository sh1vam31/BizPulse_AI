from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.auth import UserRole

COMMON_DOMAIN_TYPOS = {
    # Gmail
    "gmaill.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmaik.com": "gmail.com",
    "gmaio.com": "gmail.com",
    "gmaiil.com": "gmail.com",
    "gmailll.com": "gmail.com",
    "gemail.com": "gmail.com",
    "gmail.co": "gmail.com",
    "gmail.con": "gmail.com",
    "googlemail.con": "googlemail.com",
    # Yahoo
    "yaho.com": "yahoo.com",
    "yahooo.com": "yahoo.com",
    "yahoo.con": "yahoo.com",
    "yaho.co": "yahoo.com",
    "ymail.con": "ymail.com",
    # Outlook / Hotmail
    "outlok.com": "outlook.com",
    "outloo.com": "outlook.com",
    "ootlook.com": "outlook.com",
    "outlook.con": "outlook.com",
    "outlock.com": "outlook.com",
    "hotmial.com": "hotmail.com",
    "hotmaill.com": "hotmail.com",
    "hotmali.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "hotmai.com": "hotmail.com",
    # iCloud
    "iclould.com": "icloud.com",
    "icoud.com": "icloud.com",
    "icloud.con": "icloud.com",
}


def check_email_domain(email_str: str) -> str:
    if "@" not in email_str:
        return email_str
    domain = email_str.split("@")[-1].lower().strip()

    if domain in COMMON_DOMAIN_TYPOS:
        suggested = COMMON_DOMAIN_TYPOS[domain]
        raise ValueError(f"Did you mean @{suggested}? Please check your email spelling.")

    if domain.endswith(".con"):
        corrected = domain[:-4] + ".com"
        raise ValueError(f"Did you mean @{corrected}? Please check your email spelling.")

    return email_str


def validate_person_name(name_str: str) -> str:
    cleaned = name_str.strip()
    if re.search(r'\d', cleaned):
        raise ValueError("Full name cannot contain numbers. Please enter a valid name (e.g., John Doe).")

    if not re.match(r"^[A-Za-zÀ-ÿ\s\.\'-]+$", cleaned):
        raise ValueError("Full name must contain only letters, spaces, hyphens, and apostrophes.")

    letters = re.findall(r'[A-Za-zÀ-ÿ]', cleaned)
    if len(letters) < 2:
        raise ValueError("Full name must contain at least 2 letters.")

    return cleaned


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_person_name(v)

    @field_validator("email")
    @classmethod
    def validate_email_typo(cls, v: EmailStr) -> EmailStr:
        check_email_domain(str(v))
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_typo(cls, v: EmailStr) -> EmailStr:
        check_email_domain(str(v))
        return v


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

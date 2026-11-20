from typing import Literal

from pydantic import BaseModel, EmailStr


class WorkspaceMemberCreate(BaseModel):
    email: EmailStr
    role: Literal["manager", "member"] = "member"

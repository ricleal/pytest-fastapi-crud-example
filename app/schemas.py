from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class UserBaseSchema(BaseModel):

    id: UUID | None = None
    first_name: str = Field(
        None, description="The first name of the user", example="John"
    )
    last_name: str = Field(None, description="The last name of the user", example="Doe")
    address: str | None = None
    email: str = Field(None, description="User email")
    role: str = Field(None, description="The role of the user", example="admin")
    activated: bool = False
    createdAt: datetime | None = None
    updatedAt: datetime | None = None

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True


class Status(Enum):
    Success = "Success"
    Failed = "Failed"


class UserResponse(BaseModel):
    Status: Status
    User: UserBaseSchema


class GetUserResponse(BaseModel):
    Status: Status
    User: UserBaseSchema


class ListUserResponse(BaseModel):
    status: Status
    results: int
    users: List[UserBaseSchema]


class DeleteUserResponse(BaseModel):
    Status: Status
    Message: str
    Message: str


class AuthResponse(BaseModel):
    id_token: str

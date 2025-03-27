import uuid

from sqlalchemy import TIMESTAMP, Boolean, Column, String
from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType

from app.database import Base


class User(Base):
    __tablename__ = "users"

    # Primary key and GUID type
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)

    # String types with appropriate non-null constraints
    first_name = Column(
        String(255), nullable=False, index=True
    )  # Indexed for faster searches

    last_name = Column(
        String(255), nullable=False, index=True
    )  # Indexed for faster searches

    address = Column(String(255), nullable=True)

    # Email with unique constraint and non-null
    email = Column(String(255), nullable=False, unique=True, index=True)

    # role
    role = Column(String(255), nullable=False)

    # Boolean type with a default value
    activated = Column(Boolean, nullable=False, default=True)

    # Timestamps with timezone support
    createdAt = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updatedAt = Column(TIMESTAMP(timezone=True), default=None, onupdate=func.now())

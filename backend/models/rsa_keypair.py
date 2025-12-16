"""
Модель RSA ключевой пары
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.database import Base


class RSAKeyPair(Base):
    __tablename__ = "rsa_keypairs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    key_id = Column(String, unique=True, nullable=False, index=True)

    # RSA parameters (stored as strings due to size)
    p = Column(Text, nullable=False)
    q = Column(Text, nullable=False)
    n = Column(Text, nullable=False)
    e = Column(Text, nullable=False)
    d = Column(Text, nullable=False)  # Encrypted

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", back_populates="rsa_keypairs")

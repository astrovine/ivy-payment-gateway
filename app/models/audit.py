from .base import Base, Column, Integer, String, DateTime, ForeignKey, func


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    merchant_id = Column(String, nullable=True)

    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)

    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    changes = Column(String, nullable=True)
    extra_data = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

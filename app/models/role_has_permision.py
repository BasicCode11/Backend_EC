from sqlalchemy import Table, Column, Integer, ForeignKey
from app.database import Base

role_has_permission = Table(
    "role_has_permissions",
    Base.metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
)

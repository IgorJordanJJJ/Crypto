from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from typing import Any


class Base(DeclarativeBase):
    metadata = MetaData()
    
    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
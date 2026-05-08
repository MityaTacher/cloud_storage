from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, func, BigInteger, Float
from datetime import datetime

class StorageNode(Base):
    __tablename__ = 'storage_nodes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    internal_address: Mapped[str] = mapped_column(String, nullable=False, server_default='http://storage-1:8001')
    total_space_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    free_space_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    rx_bytes_per_sec: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tx_bytes_per_sec: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ram_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    files: Mapped[list['File']] = relationship('File', back_populates='node')

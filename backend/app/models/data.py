from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid, utc_now


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # CSV, Excel, Database, API
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    import_jobs = relationship("DataImportJob", back_populates="source", cascade="all, delete-orphan")


class DataImportJob(Base):
    __tablename__ = "data_import_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    records_processed = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="import_jobs")
    errors = relationship("ImportErrorLog", back_populates="job", cascade="all, delete-orphan")


class ImportErrorLog(Base):
    __tablename__ = "import_error_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    import_job_id = Column(String(36), ForeignKey("data_import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    column_name = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    job = relationship("DataImportJob", back_populates="errors")


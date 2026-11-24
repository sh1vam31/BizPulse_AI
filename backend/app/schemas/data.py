from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DataSourceBase(BaseModel):
    source_name: str = Field(..., min_length=2, max_length=255)
    source_type: str = Field(..., max_length=50)


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceResponse(DataSourceBase):
    id: str
    organization_id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ImportErrorLogResponse(BaseModel):
    id: str
    import_job_id: str
    row_number: int
    column_name: Optional[str] = None
    error_message: str
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DataImportJobResponse(BaseModel):
    id: str
    source_id: str
    file_name: str
    records_processed: int
    records_failed: int
    status: str
    error_summary: Optional[str] = None
    created_at: datetime
    errors: Optional[List[ImportErrorLogResponse]] = []
    model_config = ConfigDict(from_attributes=True)


class DataValidationResponse(BaseModel):
    is_valid: bool
    detected_entity_type: Optional[str] = None
    total_rows: int
    valid_rows: int
    invalid_rows: int
    column_mappings: Dict[str, str]
    errors: List[Dict[str, Any]] = []
    sample_preview: List[Dict[str, Any]] = []


class UploadResponse(BaseModel):
    job_id: str
    file_name: str
    entity_type: str
    status: str
    records_processed: int
    records_failed: int
    message: str


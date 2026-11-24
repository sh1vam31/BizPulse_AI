import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.api.deps import get_current_active_user, get_db
from app.models.auth import User
from app.models.data import DataImportJob, DataSource
from app.schemas.data import (
    DataImportJobResponse,
    DataSourceResponse,
    DataValidationResponse,
    UploadResponse,
)
from app.services.ingestion_service import (
    detect_schema,
    execute_ingestion,
    parse_file_to_dataframe,
    validate_dataframe,
)

router = APIRouter()


@router.post("/validate", response_model=DataValidationResponse)
async def validate_file(
    file: UploadFile = File(...),
    entity_type: Optional[str] = Form(None),
    column_mapping: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
):
    try:
        contents = await file.read()
        df = await run_in_threadpool(parse_file_to_dataframe, contents, file.filename or "upload.csv")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse uploaded file: {str(e)}",
        )

    # Detect schema or use provided mapping
    mapping = {}
    if column_mapping:
        try:
            mapping = json.loads(column_mapping)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="column_mapping must be valid JSON object",
            )

    detected_type, detected_mapping = detect_schema(list(df.columns))
    target_entity = entity_type or detected_type
    final_mapping = {**detected_mapping, **mapping}

    if not target_entity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not automatically detect entity type from columns. Please specify entity_type explicitly.",
        )

    result = await run_in_threadpool(validate_dataframe, df, target_entity, final_mapping)
    return result


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    entity_type: Optional[str] = Form(None),
    column_mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        contents = await file.read()
        df = await run_in_threadpool(parse_file_to_dataframe, contents, file.filename or "upload.csv")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}",
        )

    # Resolve schema and mappings
    custom_mapping = {}
    if column_mapping:
        try:
            custom_mapping = json.loads(column_mapping)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON for column_mapping",
            )

    detected_type, detected_mapping = detect_schema(list(df.columns))
    target_entity = entity_type or detected_type
    final_mapping = {**detected_mapping, **custom_mapping}

    if not target_entity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine entity type. Please specify entity_type (e.g. products, customers, suppliers, sales).",
        )

    # Get or create data source for user's organization
    data_source = db.query(DataSource).filter(
        DataSource.organization_id == current_user.organization_id,
        DataSource.source_name == f"Upload: {target_entity}",
    ).first()

    if not data_source:
        file_ext = "CSV" if (file.filename or "").lower().endswith(".csv") else "Excel"
        data_source = DataSource(
            organization_id=current_user.organization_id,
            source_name=f"Upload: {target_entity}",
            source_type=file_ext,
            status="ACTIVE",
        )
        db.add(data_source)
        db.flush()

    # Create Import Job
    import_job = DataImportJob(
        source_id=data_source.id,
        file_name=file.filename or "uploaded_dataset",
        records_processed=0,
        records_failed=0,
        status="PROCESSING",
    )
    db.add(import_job)
    db.commit()
    db.refresh(import_job)

    # Execute ingestion
    try:
        processed, failed = await run_in_threadpool(
            execute_ingestion,
            db=db,
            organization_id=current_user.organization_id,
            df=df,
            entity_type=target_entity,
            mapping=final_mapping,
            job=import_job,
        )

        import_job.records_processed = processed
        import_job.records_failed = failed
        import_job.status = "COMPLETED" if failed == 0 or (processed / (processed + failed) > 0.5) else "FAILED"
        if failed > 0:
            import_job.error_summary = f"{failed} rows failed validation/insertion."
        db.commit()

        return UploadResponse(
            job_id=import_job.id,
            file_name=import_job.file_name,
            entity_type=target_entity,
            status=import_job.status,
            records_processed=processed,
            records_failed=failed,
            message=f"Successfully processed {processed} records ({failed} failed).",
        )
    except Exception as e:
        import_job.status = "FAILED"
        import_job.error_summary = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data ingestion failed: {str(e)}",
        )


@router.get("/sources", response_model=List[DataSourceResponse])
def get_data_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sources = db.query(DataSource).filter(
        DataSource.organization_id == current_user.organization_id
    ).order_by(DataSource.created_at.desc()).all()
    return sources


@router.get("/imports", response_model=List[DataImportJobResponse])
def get_import_jobs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    jobs = (
        db.query(DataImportJob)
        .join(DataSource, DataImportJob.source_id == DataSource.id)
        .filter(DataSource.organization_id == current_user.organization_id)
        .order_by(DataImportJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return jobs


@router.get("/imports/{job_id}", response_model=DataImportJobResponse)
def get_import_job_details(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = (
        db.query(DataImportJob)
        .join(DataSource, DataImportJob.source_id == DataSource.id)
        .filter(
            DataImportJob.id == job_id,
            DataSource.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found",
        )
    return job


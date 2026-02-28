from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.database import get_db
from backend.models.collection_job import CollectionJob

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CollectionJob).order_by(desc(CollectionJob.created_at)).limit(limit)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": j.id, "job_type": j.job_type, "status": j.status,
            "seed_keyword": j.seed_keyword, "target": j.target,
            "keywords_found": j.keywords_found, "progress": j.progress,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.get("/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(CollectionJob, job_id)
    if not job:
        return {"error": "Job not found"}
    return {
        "id": job.id, "job_type": job.job_type, "status": job.status,
        "seed_keyword": job.seed_keyword, "target": job.target,
        "keywords_found": job.keywords_found, "progress": job.progress,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }

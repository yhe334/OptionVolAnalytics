from typing import Optional
from sqlalchemy.orm import Session
from iv_hv_analytics.persistence.models import VolRequest, VolResult

class VolRepository:
    def get_result_by_hash(self, db: Session, request_hash: str) -> Optional[VolResult]:
        row = (
            db.query(VolResult)
            .filter(VolResult.request_hash == request_hash)
            .order_by(VolResult.created_at.desc())
            .first()
        )
        return row.result_json if row else None

    def ensure_request(self, db: Session, request_hash: str, params_json: str) -> None:
        existing = (
            db.query(VolRequest)
            .filter(VolRequest.request_hash == request_hash)
            .first()
        )
        if existing:
            return
        db.add(VolRequest(request_hash=request_hash, params_json=params_json))
        db.commit()

    def save_result(self, db: Session, request_hash: str, result_json: str) -> None:
        db.add(VolResult(request_hash=request_hash, result_json=result_json))
        db.commit()
        
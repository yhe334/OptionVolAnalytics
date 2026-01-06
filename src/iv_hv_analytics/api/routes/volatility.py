from fastapi import APIRouter, Depends
from iv_hv_analytics.api.schemas import VolatilityRequest, VolatilityResponse
from iv_hv_analytics.services.volatility_service import VolatilityService
from iv_hv_analytics.api.deps import get_db
from iv_hv_analytics.persistence.repository import VolRepository
from iv_hv_analytics.cache.memory import MemoryCache
from sqlalchemy.orm import Session
from iv_hv_analytics.clients.ibkr_client import IbkrClient, IbkrConfig





router = APIRouter(prefix='/volatility', tags=['volatility'])

_repo = VolRepository()
_cache = MemoryCache()

_ibkr = IbkrClient(IbkrConfig(host='127.0.01',port=7496,client_id=1))
_service = VolatilityService(repo=_repo, cache=_cache, ibkr=_ibkr, cache_ttl_seconds=300)

@router.post('/iv-hv', response_model=VolatilityResponse)
def iv_hv(req: VolatilityRequest, db: Session = Depends(get_db)) -> VolatilityResponse:
    return _service.get_iv_hv_spread(db, req)
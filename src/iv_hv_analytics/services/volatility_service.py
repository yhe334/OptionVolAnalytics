from datetime import timedelta, date
from iv_hv_analytics.api.schemas import VolatilityRequest, VolatilityResponse, VolatilityPoint
from typing import List,Optional,Tuple
import json
from sqlalchemy.orm import Session
from iv_hv_analytics.cache.base import Cache
from iv_hv_analytics.core.idempotency import request_to_canonical_json, compute_request_hash    
from iv_hv_analytics.persistence.repository import VolRepository
from iv_hv_analytics.clients.ibkr_client import IbkrClient
from iv_hv_analytics.domain.volatility import rolling_hv


class VolatilityService:
    def __init__(self, repo: VolRepository, cache: Cache, ibkr: IbkrClient,cache_ttl_seconds: int = 300) -> None:
        self._repo = repo
        self._cache = cache
        self._ibkr = ibkr
        self._ttl = cache_ttl_seconds
    def get_iv_hv_spread(self, db: Session, req: VolatilityRequest) -> VolatilityResponse:
        params_json = request_to_canonical_json(req)
        req_hash = compute_request_hash(params_json)

        #1) Cache
        cached = self._cache.get(req_hash)
        if cached:
             return VolatilityResponse.parse_obj(json.loads(cached))
        
        #2) DB
        existing = self._repo.get_result_by_hash(db,req_hash)
        if existing:
            self._cache.set(req_hash, existing, ttl_seconds=self._ttl)
            return VolatilityResponse.parse_obj(json.loads(existing))
        
        #3) Compute (stubbed for now)
        resp = self._compute_real_hv_stub_iv(req)

        #4) Persist idempotently
        self._repo.ensure_request(db,req_hash,params_json)
        result_json = resp.json()
        self._repo.save_result(db,req_hash,result_json)

        #5) Cache
        self._cache.set(req_hash,result_json,ttl_seconds=self._ttl)
        return resp

    def _compute_real_hv_stub_iv(self, req: VolatilityRequest) -> VolatilityResponse:
        bars: List[Tuple[date,float]] = self._ibkr.fetch_daily_dated_closes(
            symbol=req.symbol,
            start_date=req.start_date,
            end_date=req.end_date,
        )

        dates = [d for (d,_) in bars]
        prices = [p for (_,p) in bars]

        hv_series: List[Optional[float]] = rolling_hv(prices,window=req.hv_window,trading_days=252)
        
        iv_snapshot = self._ibkr.fetch_iv_snapshot(
                symbol=req.symbol,
                asof=req.end_date,
                target_dte_days=req.iv_target_days,
                iv_moneyness=req.iv_moneyness,
        )

        points: List[VolatilityPoint] = []

        for d, hv in zip(dates,hv_series):
            iv = None
            spread = None
            if hv is not None:
                hv_val = float(hv)
            
            else:
                hv_val = None
          
            points.append(VolatilityPoint(
                date=d,
                hv=hv_val,
                iv=iv,
                spread=spread
            ))
        return VolatilityResponse(
                symbol=req.symbol.upper(),
                hv_window=req.hv_window,
                iv_target_days=req.iv_target_days,
                points=points,
                meta={"mode":"real_hv_iv_snapshot","source" : "ibkr"}
        )
    
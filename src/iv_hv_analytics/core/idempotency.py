import hashlib
import json
from iv_hv_analytics.api.schemas import VolatilityRequest

def request_to_canonical_json(req: VolatilityRequest) -> str:
    payload = {
        "symbol": req.symbol.upper(),
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "hv_window": req.hv_window,
        "iv_target_days": req.iv_target_days,
        "iv_moneyness": req.iv_moneyness,
    }
    return json.dumps(payload, separators=(',', ':'))

def compute_request_hash(cannonical_json: str) -> str:
    return hashlib.sha256(cannonical_json.encode('utf-8')).hexdigest()


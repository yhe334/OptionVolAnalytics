from __future__ import annotations

import math
from typing import Optional, List

def log_returns(prices: List[float]) -> List[float]:
    if len(prices) < 2:
        return []
    rets: List[float] = []
    prev = prices[0]

    if prev <= 0:
        raise ValueError("Prices must be positive to compute log returns.")
    for p in prices[1:]:
        if p <= 0:
            raise ValueError("Prices must be positive to compute log returns.")
        r = math.log(p / prev)
        rets.append(r)
        prev = p
    return rets

def rolling_hv(prices: List[float], window: int, trading_days: int = 252) -> List[Optional[float]]:
    
    # Annnualized HV = stdev(log_returns_window) * sqrt(trading_days)

    if window < 2:
        raise ValueError("Window size must be at least 2.")
    n = len(prices)
    if n == 0:
        return []
    rets = log_returns(prices)
    out: List[Optional[float]] = [None] * n 

    req = window - 1
    if len(rets) < req:
        return out
    
    sqrt_td = math.sqrt(trading_days)

    for i in range(window - 1, n):
        start = i - req
        end = i
        w = rets[start:end]

        m = sum(w) / len(w)
        var = 0.0
        for x in w:
            var += (x - m) ** 2
        
        if len(w) < 2:
            out[i] = None
            continue
        var /= (len(w) - 1)
        out[i] = math.sqrt(var) * sqrt_td

    return out


import math
import pytest

from iv_hv_analytics.domain.volatility import rolling_hv,log_returns

def test_log_returns_constant_prices():
    prices = [100.0, 100.0, 100.0]
    rets = log_returns(prices)
    assert rets == [0.0, 0.0]

def test_rolling_hv_constant_prices_is_zero_after_window():
    prices = [100.0] * 30
    hv = rolling_hv(prices, window=20,trading_days=252)
    
    assert all(x is None for x in hv[:19])

    for x in hv[19:]:
        assert x is not None
        assert abs(x - 0.0) < 1e-12

def test_rolling_hv_invalid_window():
    with pytest.raises(ValueError):
        rolling_hv([100.0, 101.0], window=1)

def test_log_returns_requires_positive_prices():
    with pytest.raises(ValueError):
        log_returns([100.0, 0])

    
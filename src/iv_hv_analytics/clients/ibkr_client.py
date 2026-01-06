from __future__ import annotations
import asyncio
from dataclasses import dataclass
import pandas as pd
from typing import Optional, List,Tuple
from typing_extensions import Literal
from datetime import date,datetime,time
import math
from ib_insync import IB, Stock, util,Option

def _ensure_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

@dataclass
class IbkrConfig:
    host: str = '127.0.0.1'
    port: int = 7496
    client_id: int = 7

def _closest(items, target, key=lambda x: x):
    return min(items, key=lambda x: abs(key(x) - target))

class IbkrClient:
    def __init__(self, cfg: Optional[IbkrConfig] = None) -> None:
        self._cfg = cfg or IbkrConfig()

    def fetch_daily_dated_closes(
            self,symbol,start_date,end_date,exchange = 'SMART',currency = 'USD'
    ) -> List[Tuple[date,float]]:
        
        _ensure_event_loop()
        if end_date < start_date:
            raise ValueError("end_date must be >= start_date")
        
        days = (end_date - start_date).days + 10
        duration = f"{days} D"

        ib = IB()
        ib.connect(self._cfg.host,self._cfg.port,self._cfg.client_id,timeout=5)
        contract = Stock(symbol,exchange,currency)
        try:
            bars = ib.reqHistoricalData(
                contract,
                endDateTime=end_date.strftime("%Y%m%d %H:%M:%S"),
                durationStr='{} D'.format((end_date - start_date).days + 1),
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1,
            )
            if not bars:
                raise ValueError(f"No historical data returned for {symbol} from IBKR.")
            df = util.df(bars)
            df['date'] = pd.to_datetime(df['date'],errors='coerce').dt.date
            df = df.dropna(subset=['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

            if df.empty:
                raise ValueError(f"No historical data in the specified date range for {symbol} from IBKR.")
            
            out: List[Tuple[date,float]] = []
            for _, row in df.iterrows():
                out.append((row['date'], row['close']))
            
            return out
        finally:
            ib.disconnect()


    def fetch_iv_snapshot(self, symbol, asof, target_dte_days, iv_moneyness='ATM', exchange='SMART', currency='USD') -> float:
        
        _ensure_event_loop()
        ib = IB()
        ib.connect(self._cfg.host,self._cfg.port,self._cfg.client_id,timeout=5)
        try:
            try:
               ib.reqMarketDataType(3)
            except Exception:
                pass
           
            underlying = Stock(symbol, exchange, currency)
            ib.qualifyContracts(underlying)

            end_dt = datetime.combine(asof, time(23,59,59))
            bars = ib.reqHistoricalData(
                underlying,
                endDateTime=end_dt,
                durationStr='3 D',
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1,
            )
            if not bars:
                raise ValueError(f"No historical data returned for {symbol} from IBKR.")    
            spot = float(bars[-1].close)
            if not spot or spot <= 0 or math.isnan(spot):
                raise RuntimeError(f"Invalid historical close for underlying {symbol} from IBKR: {spot}")
           
            chains = ib.reqSecDefOptParams(underlying.symbol, '', underlying.secType, underlying.conId)
            if not chains:
                raise ValueError(f"No option chain data returned for {symbol} from IBKR.")
            chain = chains[0]
            expirations = sorted(chain.expirations)
            strikes = sorted(chain.strikes)

            if not expirations or not strikes:
               raise RuntimeError(f"Option chain missing expirations/strikes for {symbol}.")
           
            def exp_to_date(s):
               return datetime.strptime(s, "%Y%m%d").date()
            
            exp_dates = [exp_to_date(e) for e in expirations]
            target_ord = asof.toordinal() + int(target_dte_days)
            chosen_exp = min(exp_dates, key=lambda d: abs(d.toordinal() - target_ord))
           
            if iv_moneyness == 'ATM':
               target_strike = spot
            else:
                target_strike = spot * float(iv_moneyness)
            
            chosen_strike = min(strikes, key=lambda k: abs(k - target_strike))
           
            opt = Option(symbol, chosen_exp.strftime("%Y%m%d"), chosen_strike, 'C', exchange)
            ib.qualifyContracts(opt)
           
            t = ib.reqMktData(opt, '', True, False)
           
            ib.sleep(2.0)
            
            def _extract_iv(ticker):
               for g in (ticker.modelGreeks, ticker.bidGreeks, ticker.askGreeks, ticker.lastGreeks):
                   if g and g.impliedVol is not None:
                        try:
                           v = float(g.impliedVol)
                           if v > 0 and not math.isnan(v):
                               return v
                        except Exception:
                           pass
                   return None
            iv = _extract_iv(t)
            if iv is None:
                raise RuntimeError(f"Could not retrieve valid IV for {symbol} {chosen_exp} {chosen_strike}C from IBKR.")
            return iv
        finally:
            ib.disconnect()


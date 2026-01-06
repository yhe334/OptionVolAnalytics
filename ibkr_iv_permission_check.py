import math
import asyncio
from datetime import datetime
from ib_insync import IB, Stock, util, Option

def ensure_loop():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

def exp_to_ord(exp_str: str) -> int:
    return datetime.strptime(exp_str, "%Y%m%d").toordinal()

from datetime import date, time 
def main():
    ensure_loop()
    ib = IB()
    ib.connect('127.0.0.1', 7496, clientId=1, timeout=5)
    try:
        ib.reqMarketDataType(3)
        symbol = "SPY"
        asof = date.today()
        target_dte_days = 30

        stk = Stock(symbol, 'SMART', 'USD')
        ib.qualifyContracts(stk)

        end_dt = datetime.combine(asof, time(23,59,59))
        bars = ib.reqHistoricalData(
            stk,
            endDateTime=end_dt,
            durationStr='5 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1,
        )
        if not bars:
            raise ValueError(f"No historical data returned for {symbol} from IBKR.")
        
        spot = float(bars[-1].close)
        print('Spot proxy(historical close):', spot)

        chains = ib.reqSecDefOptParams(stk.symbol, '', stk.secType, stk.conId)
        print("Chains returned:", len(chains))
        if not chains:
            raise ValueError(f"No option chain data returned for {symbol} from IBKR.")
        best = None
        best_score = -1
        for c in chains:
            score = 0
            if getattr(c, 'exchange', '') == 'SMART':
                score += 1000
            score += len(getattr(c, 'expirations', []) or [])
            score += len(getattr(c, 'strikes', []) or [])
            if score > best_score:
                best = c
                best_score = score
        expirations = sorted(best.expirations)
        strikes_all = sorted(best.strikes)

        if not expirations or not strikes_all:
            raise RuntimeError(f"Option chain missing expirations/strikes for {symbol}.")
        
        target_ord = asof.toordinal() + int(target_dte_days)
        chosen_exp = min(expirations, key=lambda e: abs(exp_to_ord(e) - target_ord))

        lo = spot * 0.5
        hi = spot * 1.5
        strikes = [s for s in strikes_all if lo <= s <= hi] or strikes_all
        chosen_strike = min(strikes, key=lambda k: abs(k - spot))

        print("Chosen expiration:", chosen_exp, "chosen strike:", chosen_strike)

        opt = Option(symbol, chosen_exp, chosen_strike, 'C', 'SMART')
        ib.qualifyContracts(opt)
        t = ib.reqMktData(opt,genericTickList='',snapshot=True,regulatorySnapshot=False)
        ib.sleep(2.0)

        def extract_iv(ticker):
            for g in (ticker.modelGreeks, ticker.bidGreeks, ticker.askGreeks, ticker.lastGreeks):
                if g and g.impliedVol is not None:
                    try:
                        iv = float(g.impliedVol)
                        if iv > 0 and not math.isnan(iv):
                            return iv
                    except Exception:
                        pass
            return None
        
        iv = extract_iv(t)

        print("modelGreeks:", t.modelGreeks)
        print("lastGreeks:", t.lastGreeks)
        if iv is None:
            raise RuntimeError(f"Could not retrieve valid IV for {symbol} {chosen_exp} {chosen_strike}C from IBKR.")
        print("Implied Volatility:", iv)
    finally:
        ib.disconnect()
        
if __name__ == "__main__":
    main()


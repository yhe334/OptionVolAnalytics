from datetime import date
from pydantic import BaseModel, Field
from typing import Optional,List,Dict, Union, Literal

class VolatilityRequest(BaseModel):
    symbol: str = Field(...,examples=['SPY'])
    start_date: date = Field(...,description='Historical data start date (YYYY-MM-DD)')
    end_date: date = Field(...,description='Historical data end date (YYYY-MM-DD)')
    hv_window: int = Field(20,ge=2,le=252,description='Rolling window in trading days')
    iv_target_days: int = Field(30, ge=7, le=365, description = 'Target Option DTE for IV snapshot')
    iv_moneyness: Union[Literal['ATM'], float] = 'ATM'

class VolatilityPoint(BaseModel):
    date: date
    hv: Optional[float] = None
    iv: Optional[float] = None
    spread: Optional[float] = None # iv - hv

class VolatilityResponse(BaseModel):
    symbol: str
    hv_window: int
    iv_target_days: int
    points: List[VolatilityPoint]
    meta: Dict[str,str] = {}


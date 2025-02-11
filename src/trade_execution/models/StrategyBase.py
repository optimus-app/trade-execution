from pydantic import BaseModel
from typing import Optional
from trade_execution.models.APIConnectInfo import APIConnectInfo
from futu import *

class StrategyBase(BaseModel):
    info: APIConnectInfo = APIConnectInfo.getInstance()
    # TODO: Determine if we need quote_context here as we separate quoting and placing orders
    quote_context: OpenQuoteContext = info.quote_context
    trade_context: OpenSecTradeContext = info.trade_context
    def is_normal_trading_time(code: str) -> bool:
        pass
    
    # We can add some common logic among strategies here
    
    

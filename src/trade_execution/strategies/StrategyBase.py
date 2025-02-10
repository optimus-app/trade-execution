from pydantic import BaseModel
from typing import Optional
from futu import *

class StrategyBase(BaseModel):
    FUTU_OPEND_ADDRESS: str = "127.0.0.1"
    FUTU_OPEND_PORT: int = 11111

    TRADING_ENV: TrdEnv = TrdEnv.SIMULATE
    TRADING_MARKET: TrdMarket = TrdMarket.HK
    TRADING_PWD: str = "123456"
    TRADING_SECURITY: str = "HK.00700"
    
    quote_context: Optional[OpenQuoteContext] = None
    trade_context: Optional[OpenSecTradeContext] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quote_context = OpenQuoteContext(host=self.FUTU_OPEND_ADDRESS, port=self.FUTU_OPEND_PORT)
        self.trade_context = OpenSecTradeContext(host=self.FUTU_OPEND_ADDRESS, port=self.FUTU_OPEND_PORT)

    # This method checks if the current time is within the normal trading hours
    def is_normal_trading_time(code: str) -> bool:
        pass
    

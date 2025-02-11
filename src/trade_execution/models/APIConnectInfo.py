from pydantic import BaseModel
from typing import Optional
from futu import *

class APIConnectInfo(BaseModel):
    FUTU_OPEND_ADDRESS: Optional[str] = None
    FUTU_OPEND_PORT: Optional[int] = None

    TRADING_ENV: TrdEnv = TrdEnv.SIMULATE
    TRADING_MARKET: TrdMarket = TrdMarket.HK
    TRADING_PWD: str = "123456"
    TRADING_PERIOD: str = "1d"

    quote_context: Optional[OpenQuoteContext] = None
    trade_context: Optional[OpenSecTradeContext] = None

    _instance = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.quote_context:
            self.quote_context = OpenQuoteContext(
                host=self.FUTU_OPEND_ADDRESS, 
                port=self.FUTU_OPEND_PORT
            )
        if not self.trade_context:
            self.trade_context = OpenSecTradeContext(
                host=self.FUTU_OPEND_ADDRESS, 
                port=self.FUTU_OPEND_PORT
            )

    # Singleton pattern
    @classmethod
    def getInstance(cls, **kwargs):
        if not cls._instance:
            cls._instance = cls(**kwargs)
        return cls._instance

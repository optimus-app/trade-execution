from futu import *
from trade_execution.models.APIConnectInfo import APIConnectInfo
from pydantic import BaseModel

class OrderBook(BaseModel):
    info: APIConnectInfo = APIConnectInfo.getInstance()

    def getOrderBook(self, code: str) -> dict:
        ret, data = self.info.quote_context.get_order_book(code)
        if ret != RET_OK:
            raise Exception("Failed to get order book: %s" % data)
        return data
from futu import *
from trade_execution.models.ConnectionManager import ConnectionManager
from datetime import datetime
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.handlers.order_book_handler')

class OrderBookHandler(OrderBookHandlerBase):
    def __init__(self, loop=None):
        super().__init__()
        self.loop = loop  # Store the event loop reference
        
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logger.error(f"OrderBookHandler error: {data}")
            return ret_code, data
            
        # Process the order book data
        code = data.get('code')
        bid_list = data.get('Bid')
        ask_list = data.get('Ask')
        
        message = {
            "type": "order_book_update",
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "bid": bid_list,
            "ask": ask_list
        }
        
        # Asynchronously broadcast the order book update
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast_update(message),
                self.loop
            )
        else:
            logger.error("No running event loop available to process order book update")
            
        return ret_code, data
        
    async def _broadcast_update(self, message):
        """Broadcast order book update to all connected WebSocket clients"""
        connection_manager = ConnectionManager.getInstance()
        await connection_manager.broadcast(message)
        logger.info(f"Order book update broadcasted for {message['code']}")
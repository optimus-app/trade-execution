from futu import TradeOrderHandlerBase, RET_OK
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.handlers.order_handler')

class OrderHandler(TradeOrderHandlerBase):
    def __init__(self, ws_handler, loop=None):
        self.ws_handler = ws_handler
        self.loop = loop  # Store the event loop reference
        super().__init__()
    
    def on_recv_rsp(self, rsp_pb):
        ret, data = super(OrderHandler, self).on_recv_rsp(rsp_pb)
        if ret == RET_OK:
            # Process each order in the dataframe
            for _, row in data.iterrows():
                order_data = {
                    "order_id": row['order_id'],
                    "code": row['code'],
                    "order_status": row['order_status'],
                    "qty": row['qty'],
                    "price": row['price'],
                    "trd_side": row['trd_side']
                }
                
                # Use run_coroutine_threadsafe instead of create_task
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.ws_handler.process_order_update(order_data),
                        self.loop
                    )
                else:
                    logger.error("No running event loop available to process order update")
                
                # Log the order status
                logger.info(f"[OrderStatus] {row['order_status']} for {row['code']}, ID: {row['order_id']}")
        
        return ret, data
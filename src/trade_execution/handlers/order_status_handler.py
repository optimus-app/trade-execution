from datetime import datetime
from trade_execution.models.ConnectionManager import ConnectionManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.handlers.order_status_handler')

class OrderStatusHandler:
    @staticmethod
    async def process_order_update(order_data):
        """Process order status updates from Futu API and broadcast to WebSocket clients"""
        message = {
            "type": "order_update",
            "timestamp": datetime.now().isoformat(),
            "data": order_data
        }
        connection_manager = ConnectionManager.getInstance()
        await connection_manager.broadcast(message)
        logger.info(f"Order status update broadcasted: {order_data['order_status']}")
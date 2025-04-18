from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.models.ConnectionManager')

class ConnectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new ConnectionManager instance")
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections = []
        return cls._instance

    @classmethod
    def getInstance(cls):
        if not cls._instance:
            logger.info("Creating new ConnectionManager instance")
            cls._instance = cls()
        else:
            logger.info("Returning existing ConnectionManager instance")
        
        return cls._instance
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected")
    
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            await websocket.close()
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected")

    async def broadcast(self, message: Dict):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected_connections:
            await self.disconnect(conn)


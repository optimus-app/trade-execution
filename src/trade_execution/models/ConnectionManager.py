from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
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
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            # Safely close the connection if it's still open
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    logger.info(f"Closing WebSocket connection...")
                    await websocket.close()
            except Exception as e:
                logger.debug(f"Exception while closing WebSocket: {str(e)}")
                
            # Always remove from our active connections list
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    logger.info(f"Skipping send to disconnected WebSocket")
                    disconnected_connections.append(connection)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected_connections:
            await self.disconnect(conn)
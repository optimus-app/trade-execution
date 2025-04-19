from futu import *
from trade_execution.models.APIConnectInfo import APIConnectInfo
from pydantic import BaseModel
from typing import Dict, List, Optional

class OrderBook:
    """
    Represents a market order book for a specific security.
    Provides access to bids, asks, and market depth information.
    """
    info: APIConnectInfo = APIConnectInfo.getInstance()

    def getOrderBook(self, code: str) -> dict:
        """
        Retrieves the complete order book for a given security code
        
        Args:
            code: The security code (e.g., "HK.00700")
            
        Returns:
            dict: Order book data including bids and asks
            
        Raises:
            Exception: If order book retrieval fails
        """
        ret, data = self.info.quote_context.get_order_book(code)
        if ret != RET_OK:
            raise Exception(f"Failed to get order book: {data}")
        return data
    
    def getBids(self, code: str) -> List[Dict]:
        """
        Retrieves only the bid side of the order book
        
        Args:
            code: The security code
            
        Returns:
            List[Dict]: List of bid orders with price and volume
        """
        data = self.getOrderBook(code)
        return data['Bid']
    
    def getAsks(self, code: str) -> List[Dict]:
        """
        Retrieves only the ask side of the order book
        
        Args:
            code: The security code
            
        Returns:
            List[Dict]: List of ask orders with price and volume
        """
        data = self.getOrderBook(code)
        return data['Ask']
    
    def getMidPrice(self, code: str) -> float:
        """
        Calculates the mid-price between best bid and ask
        
        Args:
            code: The security code
            
        Returns:
            float: The mid-price
        """
        data = self.getOrderBook(code)
        if not data['Bid'] or not data['Ask']:
            raise Exception(f"Cannot calculate mid price - incomplete order book for {code}")
        best_bid = data['Bid'][0]['Price']
        best_ask = data['Ask'][0]['Price']
        return (best_bid + best_ask) / 2
    
    def getSpread(self, code: str) -> float:
        """
        Calculates the bid-ask spread
        
        Args:
            code: The security code
            
        Returns:
            float: The bid-ask spread
        """
        data = self.getOrderBook(code)
        if not data['Bid'] or not data['Ask']:
            raise Exception(f"Cannot calculate spread - incomplete order book for {code}")
        best_bid = data['Bid'][0]['Price']
        best_ask = data['Ask'][0]['Price']
        return best_ask - best_bid
import uvicorn
from trade_execution.api.server import create_app
from trade_execution.models.APIConnectInfo import APIConnectInfo

# Configure Futu OpenD connection
APIConnectInfo.getInstance(
    FUTU_OPEND_ADDRESS="127.0.0.1",  # Default for local OpenD
    FUTU_OPEND_PORT=11111            # Default port, adjust if needed
)

app = create_app()

if __name__ == "__main__":
    uvicorn.run("trade_execution.main:app", host="0.0.0.0", port=8000, reload=True)
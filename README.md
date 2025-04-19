# Trade Execution API

This repo serves as a server for the main backend to execute trades. It uses FastAPI, FutuAPI v9.0 and Pantsbuild for the build system. This is intended to be hosted in AWS EC2 and accessed through API Gateway.

# Main functionalities

- Submit trades through FutuAPI
- Retrieve historical orders
- Perform backtesting through FastQuant library

# How to run

```
pants run src/trade_execution/main.py
```






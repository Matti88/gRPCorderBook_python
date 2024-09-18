import grpc
import ticker_service_pb2
import ticker_service_pb2_grpc
import random # For random price generation
import time

def get_tickers(stub):
    """Get available tickers from the server."""
    request = ticker_service_pb2.TickerRequest()
    response = stub.GetTickers(request)
    print("Available Tickers:")
    for ticker in response.tickers:
        print(f"{ticker.symbol}: {ticker.name}")
    return response.tickers

def submit_limit_order(stub, ticker_symbol, side, price, quantity):
    """Submit a limit order."""
    request = ticker_service_pb2.LimitOrderRequest(
        ticker_symbol=ticker_symbol,
        side=side,
        price=price,
        quantity=quantity
    )
    response = stub.SubmitLimitOrder(request)
    print(f"Limit Order Submitted. Order ID: {response.order_id}")

def submit_market_order(stub, ticker_symbol, side, quantity):
    """Submit a market order."""
    request = ticker_service_pb2.MarketOrderRequest(
        ticker_symbol=ticker_symbol,
        side=side,
        quantity=quantity
    )
    response = stub.SubmitMarketOrder(request)
    print(f"Market Order Submitted. Order ID: {response.order_id}")

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = ticker_service_pb2_grpc.TickerServiceStub(channel)

        # 1. Get available tickers
        ticker_list = get_tickers(stub)

        while True:
            # 2. Generate random order for each ticker
            for ticker in ticker_list:
                side = random.choice(["buy", "sell"])  # Randomly choose buy or sell
                price_offset = random.randint(1, 15)  # Random offset from 150
                price = 150 + (price_offset if side == "buy" else -price_offset)
                quantity = random.randint(100, 200)  # Random quantity between 100 and 200
                submit_limit_order(stub, ticker.symbol, side, price, quantity)

            # 3. Wait for 0.5 seconds before next round
            time.sleep(0.5)

if __name__ == '__main__':
    run()



# import grpc
# import time
# import ticker_service_pb2
# import ticker_service_pb2_grpc
# import random  # For random order quantity and price generation

# def get_tickers(stub):
#     """Get available tickers from the server."""
#     request = ticker_service_pb2.TickerRequest()
#     response = stub.GetTickers(request)
#     print("Available Tickers:")
#     for ticker in response.tickers:
#         print(f"{ticker.symbol}: {ticker.name}")
#     return response.tickers

# def submit_limit_order(stub, ticker_symbol, side, price, quantity):
#     """Submit a limit order."""
#     request = ticker_service_pb2.LimitOrderRequest(
#         ticker_symbol=ticker_symbol,
#         side=side,
#         price=price,
#         quantity=quantity
#     )
#     response = stub.SubmitLimitOrder(request)
#     print(f"Limit Order Submitted for {ticker_symbol} ({side}): Order ID: {response.order_id}")

# def run():
#     with grpc.insecure_channel('localhost:50051') as channel:
#         stub = ticker_service_pb2_grpc.TickerServiceStub(channel)

#         # 1. Get available tickers
#         ticker_list = get_tickers(stub)

#         while True:
#             # 2. Generate random order for each ticker
#             for ticker in ticker_list:
#                 side = random.choice(["buy", "sell"])  # Randomly choose buy or sell
#                 price_offset = random.randint(1, 15)  # Random offset from 150
#                 price = 150 + (price_offset if side == "buy" else -price_offset)
#                 quantity = random.randint(100, 200)  # Random quantity between 100 and 200
#                 submit_limit_order(stub, ticker.symbol, side, price, quantity)

#             # 3. Wait for 0.5 seconds before next round
#             time.sleep(0.5)

# if __name__ == '__main__':
#     run()
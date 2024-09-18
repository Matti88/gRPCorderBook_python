import grpc
import ticker_service_pb2
import ticker_service_pb2_grpc
import random # For random price generation


def get_tickers(stub):
    """Get available tickers from the server."""
    request = ticker_service_pb2.TickerRequest()
    response = stub.GetTickers(request)
    print("Available Tickers:")
    for ticker in response.tickers:
        print(f"{ticker.symbol}: {ticker.name}")
    return response.tickers

def stream_market_data(stub, ticker_symbol):
    """Stream market data for a specific ticker."""
    request = ticker_service_pb2.TickerRequest(ticker_symbol=ticker_symbol)
    for market_data in stub.ConnectToMarketData(request):
        print(f"Market Data for {market_data.ticker_symbol}: Bid {market_data.best_bid_price} Ask {market_data.best_ask_price}")

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
        get_tickers(stub)

        # 2. Submit limit order
        for i in range(5):
            print("\nSubmitting Limit Order (sell side):")
            amount = 150 + random.choice([-1, 1]) * random.randint(1, 14)
            submit_limit_order(stub, "GOOGL", "buy",amount , 10)
        
        for i in range(5):
            print("\nSubmitting Limit Order (sell side):")
            amount = 150 + random.choice([-1, 1]) * random.randint(1, 25)
            submit_limit_order(stub, "GOOGL", "sell", amount, 10)
    
        # 3. Stream market data for a given ticker
        print("\nStreaming Market Data for GOOGL:")
        stream_market_data(stub, "GOOGL")

        # 4. Submit market order
        print("\nSubmitting Market Order:")
        submit_market_order(stub, "GOOGL", "sell", 5)

if __name__ == '__main__':
    run()

import grpc
import ticker_service_pb2
import ticker_service_pb2_grpc
import random
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
    print(f"Limit Order Submitted. Order ID: {response.order_id}, Side: {side}, Ticker: {ticker_symbol}, Price: {price}, Quantity: {quantity}")

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = ticker_service_pb2_grpc.TickerServiceStub(channel)

        # 1. Get available tickers
        ticker_list = get_tickers(stub)

        # Create different prices for each ticker by mapping them to a base price
        ticks = [tick.symbol for tick in ticker_list]
        tickers_price_map = dict(zip(ticks, [100, 500, 3000]))

        for count in range(50):
            for ticker in ticker_list:

                base_price = tickers_price_map[ticker.symbol]
                offset_range = base_price * 0.2
                price_offset = random.uniform(0, offset_range)  # Random offset between 0 and 20% of the base price

                # Alternate buy and sell orders for symmetry
                for side in ["buy", "sell"]:
                    # Define price close to the base price with a small deviation
                    if side == "buy":
                        price = base_price - (price_offset)  # Buy orders slightly above base
                    else:
                        price = base_price + (price_offset) # Sell orders slightly below base

                    price = round(price, 0)  # Round to 2 decimal places for precision
                    quantity = 5  # Use a constant quantity for symmetry

                    print(f"\nSubmitting Limit Order ({side}): Ticker: {ticker.symbol}, Price: {price}, Quantity: {quantity}")
                    submit_limit_order(stub, ticker.symbol, side, price, quantity)

            # 3. Wait for 1 second before the next round of orders
            time.sleep(1)

if __name__ == '__main__':
    run()

 
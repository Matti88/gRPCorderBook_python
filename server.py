import asyncio
import heapq
import itertools
import grpc
from concurrent import futures
import time

import ticker_service_pb2
import ticker_service_pb2_grpc



# Hardcoded tickers and market data for simplicity
TICKERS = [
    ticker_service_pb2.TickerInfo(symbol="AAPL", name="Apple Inc."),
    ticker_service_pb2.TickerInfo(symbol="GOOGL", name="Alphabet Inc."),
    ticker_service_pb2.TickerInfo(symbol="AMZN", name="Amazon Inc."),
]


class Order:
    def __init__(self, order_id, order_type, price, symbol, name, quantity):
        self.symbol = symbol
        self.name = name
        self.order_id = order_id
        self.order_type = order_type  # 'buy' or 'sell'
        self.price = price  # None for market orders
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.order_id}, {self.order_type}, {self.price}, {self.quantity})"

    def __lt__(self, other):
        # Define comparison for heapq: smaller order ID gets priority if prices are equal
        return self.order_id < other.order_id

class OrderBook:
    def __init__(self, symbol, name):
        self.symbol = symbol
        self.name = name
        self.buy_orders = []  # Max heap for buy orders (store negative prices for max-heap behavior)
        self.sell_orders = []  # Min heap for sell orders
        self.best_avg_price = None  # Store average price between best buy and sell orders
        self.matched_trades = []  # Store latest matched trades
        self.order_id_counter = itertools.count(1)  # Automatic order ID generator

    def add_limit_order(self, order_type, price, quantity):
        if order_type not in ['buy', 'sell']:
            raise ValueError(f"Unknown order type: {order_type}")
            
        order_id = next(self.order_id_counter)
        order = Order(order_id, order_type, price, self.symbol, self.name, quantity)

        if order_type == 'buy':
            heapq.heappush(self.buy_orders, (-order.price, order))  # Max heap (negative prices)
        else:
            heapq.heappush(self.sell_orders, (order.price, order))  # Min heap

        self.update_best_avg_price()
        return order_id  # Return the generated order ID

    def add_market_order(self, order_type, quantity):
        if order_type not in ['buy', 'sell']:
            raise ValueError(f"Unknown order type: {order_type}")
        
        order_id = next(self.order_id_counter)
        order = Order(order_id, order_type, None, self.symbol, self.name, quantity)

        if order_type == 'buy':
            self._execute_market_buy_order(order)
        else:
            self._execute_market_sell_order(order)

        return order_id  # Return the generated order ID

    def _execute_market_buy_order(self, order):
        while self.sell_orders and order.quantity > 0:
            best_sell = self.sell_orders[0][1]  # Get the best sell order (lowest price)
            if best_sell.quantity <= order.quantity:
                # Full match
                traded_quantity = best_sell.quantity
                heapq.heappop(self.sell_orders)  # Remove the sell order
                order.quantity -= traded_quantity
            else:
                # Partial match
                traded_quantity = order.quantity
                best_sell.quantity -= traded_quantity
                order.quantity = 0  # Fully fulfilled buy order

            # Store matched trade (price of best_sell)
            self.matched_trades.append((traded_quantity, best_sell.price))
            if len(self.matched_trades) > 5:
                self.matched_trades.pop(0)

    def _execute_market_sell_order(self, order):
        
        while self.buy_orders and order.quantity > 0:
            best_buy = self.buy_orders[0][1]  # Get the best buy order (highest price)
            if best_buy.quantity <= order.quantity:
                # Full match
                traded_quantity = best_buy.quantity
                heapq.heappop(self.buy_orders)  # Remove the buy order
                order.quantity -= traded_quantity
            else:
                # Partial match
                traded_quantity = order.quantity
                best_buy.quantity -= traded_quantity
                order.quantity = 0  # Fully fulfilled sell order

            # Store matched trade (price of best_buy)
            self.matched_trades.append((traded_quantity, best_buy.price))
            if len(self.matched_trades) > 5:
                self.matched_trades.pop(0)

    def update_best_avg_price(self):
        if self.buy_orders and self.sell_orders:
            best_buy = -self.buy_orders[0][0]  # Max of buy orders (negative price for max heap)
            best_sell = self.sell_orders[0][0]  # Min of sell orders
            self.best_avg_price = (best_buy + best_sell) / 2
        else:
            self.best_avg_price = None  # No valid avg price if no orders on both sides

    def match_orders(self):
        while self.buy_orders and self.sell_orders:
            highest_buy = heapq.heappop(self.buy_orders)[1]
            lowest_sell = heapq.heappop(self.sell_orders)[1]

            if highest_buy.price >= lowest_sell.price:
                # Match found
                traded_quantity = min(highest_buy.quantity, lowest_sell.quantity)
                highest_buy.quantity -= traded_quantity
                lowest_sell.quantity -= traded_quantity
                matched_trade = (traded_quantity, lowest_sell.price)

                # Add matched trade to the list and keep the list to the last 5 trades
                self.matched_trades.append(matched_trade)
                if len(self.matched_trades) > 5:
                    self.matched_trades.pop(0)

                # Reinsert any remaining quantities back into the order book
                if highest_buy.quantity > 0:
                    heapq.heappush(self.buy_orders, (-highest_buy.price, highest_buy))
                if lowest_sell.quantity > 0:
                    heapq.heappush(self.sell_orders, (lowest_sell.price, lowest_sell))
            else:
                # No match; reinsert the orders back into the order book
                heapq.heappush(self.buy_orders, (-highest_buy.price, highest_buy))
                heapq.heappush(self.sell_orders, (lowest_sell.price, lowest_sell))
                break  # Exit the loop since no match is possible at this time

        self.update_best_avg_price()

    def get_top_orders(self, n=3):
        """
        Get the top N buy and sell orders for display.
        Returns:
            tuple: (top_buy_orders, top_sell_orders)
        """
        top_buy_orders = [order[1] for order in self.buy_orders[:n]]
        top_sell_orders = [order[1] for order in self.sell_orders[:n]]
        return top_buy_orders, top_sell_orders

    def get_all_orders(self):
        total_buy_quantity = sum(order[1].quantity for order in self.buy_orders)
        total_sell_quantity = sum(order[1].quantity for order in self.sell_orders)
        return total_buy_quantity + total_sell_quantity

    def get_variance_of_orders(self):
        """
        Calculate the variance of orders.
        Returns:
            float: Variance of orders
        """
        total_buy_quantity = sum(order[1].quantity for order in self.buy_orders)
        total_sell_quantity = sum(order[1].quantity for order in self.sell_orders)
        mean = (total_buy_quantity + total_sell_quantity) / 2
        variance = sum((order[1].quantity - mean) ** 2 for order in self.buy_orders + self.sell_orders) / (total_buy_quantity + total_sell_quantity)
        return variance


class TickerServiceServicer(ticker_service_pb2_grpc.TickerServiceServicer):
    def __init__(self):
        # Initialize order books and list of clients
        self.order_books = {ticker.symbol: OrderBook(ticker.symbol, ticker.name) for ticker in TICKERS}
        self.clients = []  # Store queues for each connected client

    async def GetTickers(self, request, context):
        """Return a list of available tickers."""
        response = ticker_service_pb2.TickerResponse()
        if request.ticker_symbol:
            filtered_tickers = [ticker for ticker in TICKERS if ticker.symbol == request.ticker_symbol]
            response.tickers.extend(filtered_tickers)
        else:
            response.tickers.extend(TICKERS)
        
        return response  # Return the entire response directly

    async def ConnectToMarketData(self, request, context):
        """Stream market data asynchronously for a given ticker."""
        # Create a queue for this client
        queue = asyncio.Queue()
        self.clients.append(queue)

        try:
            while True:
                # Await the next market data point for this client
                market_data = await queue.get()
                yield market_data
        except asyncio.CancelledError:
            # If the client disconnects, remove the queue
            self.clients.remove(queue)
            raise

    async def broadcast_market_data(self):
        """Broadcast market data to all connected clients."""
        while True:
            for ticker_symbol, orderBook in self.order_books.items():
                bidOrders, askOrders = orderBook.get_top_orders(1)
                if bidOrders and askOrders:
                    bidOrders, askOrders = bidOrders[0], askOrders[0]
                
                    # Create market data message
                    market_data = ticker_service_pb2.MarketData(
                        ticker_symbol=ticker_symbol,
                        best_bid_price=bidOrders.price if bidOrders else 0,
                        best_ask_price=askOrders.price if askOrders else 0,
                        best_bid_quantity=bidOrders.quantity if bidOrders else 0,
                        best_ask_quantity=askOrders.quantity if askOrders else 0,
                        order_book_variance_max=orderBook.get_variance_of_orders(),
                        order_book_variance_min=orderBook.get_variance_of_orders(),
                        total_volume_quantity=orderBook.get_all_orders(),
                    )

                    # Broadcast the market data to all clients
                    for client in self.clients:
                        print("Starting broadcast for client", client)
                        await client.put(market_data)
            
            # Sleep to simulate a delay between data points
            await asyncio.sleep(1)



    async def SubmitLimitOrder(self, request, context):
        """Handle limit order submissions asynchronously."""
        # Generate the limit order and return the generated order_id
        order_id_code = self.order_books[request.ticker_symbol].add_limit_order(request.side, request.price, request.quantity)
        self.order_books[request.ticker_symbol].match_orders()  # Try to match any orders after adding

        # Since there are no async calls within, you do not need `await` here
        return ticker_service_pb2.OrderResponse(order_id=str(order_id_code))

    async def SubmitMarketOrder(self, request, context):
        """Handle market order submissions asynchronously."""
        # Generate the market order and return the generated order_id
        order_id_code = self.order_books[request.ticker_symbol].add_market_order(request.side, request.quantity)
        self.order_books[request.ticker_symbol].match_orders()  # Try to match any orders after adding

        # Return the response immediately
        return ticker_service_pb2.OrderResponse(order_id=str(order_id_code))


async def serve():
    # Create the gRPC server
    server = grpc.aio.server()
    ticker_service = TickerServiceServicer()
    ticker_service_pb2_grpc.add_TickerServiceServicer_to_server(ticker_service, server)
    
    # Bind the server to port 50051
    server.add_insecure_port('[::]:50051')
    
    # Start the server
    await server.start()
    print("Server started on port 50051")
    
    # Start broadcasting market data
    asyncio.create_task(ticker_service.broadcast_market_data())

    # Wait for server termination
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())
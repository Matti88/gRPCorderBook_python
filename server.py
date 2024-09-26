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
        self.order_id = order_id
        self.order_type = order_type
        self.price = price
        self.symbol = symbol
        self.name = name
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.order_id}, {self.order_type}, {self.price}, {self.quantity})"

    # Add comparison based on price
    def __lt__(self, other):
        # Orders are compared based on price
        if not isinstance(other, Order):
            return NotImplemented
        return self.price < other.price

    def __eq__(self, other):
        if not isinstance(other, Order):
            return NotImplemented
        return self.price == other.price


class OrderBook:
    def __init__(self, symbol, name):
        self.symbol = symbol
        self.name = name
        self.buy_orders = []  # Max heap for buy orders (store negative prices for max-heap behavior)
        self.sell_orders = []  # Min heap for sell orders
        self.best_avg_price = None  # Store average price between best buy and sell orders
        self.matched_trades = []  # Store latest matched trades
        self.order_id_counter = itertools.count(1)  # Automatic order ID generator

        self.lock = asyncio.Lock()  # Lock for synchronization

    async def get_top_orders(self, n=3):
        """
        Get the top N buy and sell orders for display.
        Returns:
            tuple: (top_buy_orders, top_sell_orders)
        """
        async with self.lock:
            # Get the top N buy orders (remember to negate the price for correct max-heap behavior)
            top_buy_orders = [(abs(price), order) for price, order in heapq.nsmallest(n, self.buy_orders, key=lambda x: x[0])]
            
            # Get the top N sell orders (min-heap)
            top_sell_orders = [(price, order) for price, order in heapq.nsmallest(n, self.sell_orders, key=lambda x: x[0])]

            return top_buy_orders, top_sell_orders

    async def add_limit_order(self, order_type, price, quantity):
        async with self.lock:
            if order_type not in ['buy', 'sell']:
                raise ValueError(f"Unknown order type: {order_type}")
            
            order_id = next(self.order_id_counter)
            order = Order(order_id, order_type, price, self.symbol, self.name, quantity)

            if order_type == 'buy':
                heapq.heappush(self.buy_orders, (-order.price, order))  # Max heap (negative prices)
            else:
                heapq.heappush(self.sell_orders, (order.price, order))  # Min heap

            self.update_best_avg_price()
            return order_id

    async def add_market_order(self, order_type, quantity):
        async with self.lock:
            if order_type not in ['buy', 'sell']:
                raise ValueError(f"Unknown order type: {order_type}")
        
            order_id = next(self.order_id_counter)
            order = Order(order_id, order_type, None, self.symbol, self.name, quantity)

            if order_type == 'buy':
                await self._execute_market_buy_order(order)
            else:
                await self._execute_market_sell_order(order)

            return order_id

    async def _execute_market_buy_order(self, order):
        while self.sell_orders and order.quantity > 0:
            best_sell = self.sell_orders[0][1]  # Get the best sell order (lowest price)
            if best_sell.quantity <= order.quantity:
                traded_quantity = best_sell.quantity
                heapq.heappop(self.sell_orders)  # Remove the sell order
                order.quantity -= traded_quantity
            else:
                traded_quantity = order.quantity
                best_sell.quantity -= traded_quantity
                order.quantity = 0

            self.matched_trades.append((traded_quantity, best_sell.price))
            if len(self.matched_trades) > 5:
                self.matched_trades.pop(0)

    async def _execute_market_sell_order(self, order):
        while self.buy_orders and order.quantity > 0:
            best_buy = self.buy_orders[0][1]  # Get the best buy order (highest price)
            if best_buy.quantity <= order.quantity:
                traded_quantity = best_buy.quantity
                heapq.heappop(self.buy_orders)  # Remove the buy order
                order.quantity -= traded_quantity
            else:
                traded_quantity = order.quantity
                best_buy.quantity -= traded_quantity
                order.quantity = 0

            self.matched_trades.append((traded_quantity, best_buy.price))
            if len(self.matched_trades) > 5:
                self.matched_trades.pop(0)

    def update_best_avg_price(self):
        if self.buy_orders and self.sell_orders:
            best_buy = -self.buy_orders[0][0]  # Remember the price is negated in the buy heap
            best_sell = self.sell_orders[0][0]
            self.best_avg_price = (best_buy + best_sell) / 2
        else:
            self.best_avg_price = None

    async def match_orders(self):
        async with self.lock:
            while self.buy_orders and self.sell_orders:
                highest_buy = heapq.heappop(self.buy_orders)[1]
                lowest_sell = heapq.heappop(self.sell_orders)[1]

                if highest_buy.price >= lowest_sell.price:
                    traded_quantity = min(highest_buy.quantity, lowest_sell.quantity)
                    highest_buy.quantity -= traded_quantity
                    lowest_sell.quantity -= traded_quantity
                    self.matched_trades.append((traded_quantity, lowest_sell.price))
                    if len(self.matched_trades) > 5:
                        self.matched_trades.pop(0)

                    if highest_buy.quantity > 0:
                        heapq.heappush(self.buy_orders, (-highest_buy.price, highest_buy))
                    if lowest_sell.quantity > 0:
                        heapq.heappush(self.sell_orders, (lowest_sell.price, lowest_sell))
                else:
                    heapq.heappush(self.buy_orders, (-highest_buy.price, highest_buy))
                    heapq.heappush(self.sell_orders, (lowest_sell.price, lowest_sell))
                    break

            self.update_best_avg_price()



class TickerServiceServicer(ticker_service_pb2_grpc.TickerServiceServicer):
    def __init__(self):
        self.order_books = {ticker.symbol: OrderBook(ticker.symbol, ticker.name) for ticker in TICKERS}
        self.clients = []  # Store tuples of (queue, ticker_symbol) for each connected client
        self.submission_locks = {}  # To track rate-limiting by client
        self.rate_limit_duration = 0.5  # Time limit between submissions (in seconds)

    async def GetTickers(self, request, context):
        response = ticker_service_pb2.TickerResponse()
        if request.ticker_symbol:
            filtered_tickers = [ticker for ticker in TICKERS if ticker.symbol == request.ticker_symbol]
            response.tickers.extend(filtered_tickers)
        else:
            response.tickers.extend(TICKERS)
        return response

    async def ConnectToMarketData(self, request, context):
        """
        Handles client connection for a specific ticker's market data.
        The client subscribes to updates for the requested ticker_symbol.
        """
        ticker_symbol = request.ticker_symbol
        print(f"Subscriber connected for ticker: {ticker_symbol}")

        queue = asyncio.Queue()
        self.clients.append((queue, ticker_symbol))  # Store both the queue and the subscribed ticker symbol

        try:
            while True:
                market_data = await queue.get()
                yield market_data
        except asyncio.CancelledError:
            self.clients.remove((queue, ticker_symbol))
            raise

    async def broadcast_market_data(self, ticker_symbol):
        """
        Broadcasts market data updates to clients subscribed to the specific ticker_symbol.
        """
        order_book = self.order_books[ticker_symbol]
        bidOrders, askOrders = await order_book.get_top_orders(1)

        if len(bidOrders) == 0 or len(askOrders) == 0:
            return

        market_data = ticker_service_pb2.MarketData(
            ticker_symbol=ticker_symbol,
            best_bid_price=bidOrders[0][1].price if bidOrders else 0,
            best_ask_price=askOrders[0][1].price if askOrders else 0,
            best_bid_quantity=bidOrders[0][1].quantity if bidOrders else 0,
            best_ask_quantity=askOrders[0][1].quantity if askOrders else 0,
        )

        # Only broadcast to clients who subscribed to this specific ticker symbol
        for client_queue, subscribed_ticker_symbol in self.clients:
            if subscribed_ticker_symbol == ticker_symbol:
                try:
                    await client_queue.put(market_data)
                except asyncio.QueueFull:
                    # Handle clients unable to keep up with updates
                    self.clients.remove((client_queue, subscribed_ticker_symbol))

    async def SubmitLimitOrder(self, request, context):
        # Rate limiting for client requests
        client_id = str(context.peer())
        last_submission = self.submission_locks.get(client_id, 0)
        current_time = time.time()

        if current_time - last_submission < self.rate_limit_duration:
            context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Rate limit exceeded")

        self.submission_locks[client_id] = current_time

        order_id_code = await self.order_books[request.ticker_symbol].add_limit_order(
            request.side, request.price, request.quantity)

        await self.order_books[request.ticker_symbol].match_orders()
     
        # Trigger market data broadcast upon a new order
        await self.broadcast_market_data(request.ticker_symbol)

        return ticker_service_pb2.OrderResponse(order_id=str(order_id_code))

    async def SubmitMarketOrder(self, request, context):
        client_id = str(context.peer())
        last_submission = self.submission_locks.get(client_id, 0)
        current_time = time.time()

        if current_time - last_submission < self.rate_limit_duration:
            context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Rate limit exceeded")

        self.submission_locks[client_id] = current_time

        order_id_code = await self.order_books[request.ticker_symbol].add_market_order(
            request.side, request.quantity)
        await self.order_books[request.ticker_symbol].match_orders()

        # Trigger market data broadcast upon a new order
        await self.broadcast_market_data(request.ticker_symbol)

        return ticker_service_pb2.OrderResponse(order_id=str(order_id_code))


async def serve():
    server = grpc.aio.server()
    ticker_service = TickerServiceServicer()
    ticker_service_pb2_grpc.add_TickerServiceServicer_to_server(ticker_service, server)
    
    server.add_insecure_port('[::]:50051')
    
    await server.start()
    print("Server started on port 50051")
    
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())

import heapq
import random
import threading
import time

    
class Order:
    def __init__(self, order_id, order_type, price, quantity):
        self.order_id = order_id
        self.order_type = order_type  # 'buy' or 'sell'
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.order_id}, {self.order_type}, {self.price}, {self.quantity})"

    def __lt__(self, other):
        # Define comparison for heapq in case of equal prices
        return self.order_id < other.order_id

class OrderBook:
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []
        self.best_avg_price = None  # Will store the average price between best buy and sell orders
        self.matched_trades = []  # Will store the latest matched trades

    def add_order(self, order):
        if order.order_type == 'buy':
            # Insert the buy order (max-heap behavior)
            heapq.heappush(self.buy_orders, (-order.price, order))
        else:
            # Insert the sell order (min-heap behavior)
            heapq.heappush(self.sell_orders, (order.price, order))
        
        self.update_best_avg_price()

    def update_best_avg_price(self):
        if self.buy_orders and self.sell_orders:
            best_buy = -self.buy_orders[0][0]  # Max of buy orders
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

                # Print match to the console
                # print(f"Matched: {traded_quantity} shares at {lowest_sell.price}")

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

def alternating_order_generator(order_book, interval=1):
    """
    Function to alternately generate buy/sell orders and add them to the order book.
    Runs in a separate thread.
    """
    order_id = 1
    is_buy = True  # Start with a buy order
    while True:
        order_type = 'buy' if is_buy else 'sell'
        price = random.randint(90, 110)
        quantity = random.randint(1, 20)
        order = Order(order_id, order_type, price, quantity)
        order_book.add_order(order)
        order_book.match_orders()
        order_id += 1
        is_buy = not is_buy  # Toggle between buy and sell orders
        time.sleep(interval)


import heapq

class Order:
    def __init__(self, order_id, order_type, price, quantity):
        self.order_id = order_id
        self.order_type = order_type  # 'buy' or 'sell'
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Order({self.order_id}, {self.order_type}, {self.price}, {self.quantity})"


class OrderBook:
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []

    def add_order(self, order):
        if order.order_type == 'buy':
            # Insert the buy order (max-heap behavior)
            heapq.heappush(self.buy_orders, (-order.price, order))
        else:
            # Insert the sell order (min-heap behavior)
            heapq.heappush(self.sell_orders, (order.price, order))

    def match_orders(self):
        while self.buy_orders and self.sell_orders:
            highest_buy = heapq.heappop(self.buy_orders)[1]
            lowest_sell = heapq.heappop(self.sell_orders)[1]

            if highest_buy.price >= lowest_sell.price:
                # Match found
                traded_quantity = min(highest_buy.quantity, lowest_sell.quantity)
                highest_buy.quantity -= traded_quantity
                lowest_sell.quantity -= traded_quantity
                print(f"Matched: {traded_quantity} shares at {lowest_sell.price}")

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

    def __repr__(self):
        return (f"Buy Orders: {[order[1] for order in self.buy_orders]}\n"
                f"Sell Orders: {[order[1] for order in self.sell_orders]}")

def main():
    order_book = OrderBook()

    # Add some orders
    order_book.add_order(Order(1, 'buy', 100, 10))
    order_book.add_order(Order(2, 'sell', 101, 5))
    order_book.add_order(Order(3, 'buy', 102, 15))
    order_book.add_order(Order(4, 'sell', 98, 10))
    order_book.add_order(Order(5, 'sell', 100, 10))

    print("Order Book before matching:")
    print(order_book)

    order_book.match_orders()

    print("\nOrder Book after matching:")
    print(order_book)

if __name__ == "__main__":
    main()

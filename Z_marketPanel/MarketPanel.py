from textual.app import App, ComposeResult
import heapq
import random
import threading
import time
from textual.widgets import Header, Footer, Label
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual.widget import Widget
from rich.table import Table


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

    def get_average_price(self):
        """Fetch the current average price from the order book."""
        return self.best_avg_price
        

    def get_latest_trades(self):
        """Fetch the last 5 matched trades from the order book."""
        return self.matched_trades[-5:]
        



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


class OrderBookWidget(Widget):
    """Custom widget to display the order book using Rich's table."""
    
    def __init__(self, order_book: OrderBook, **kwargs):
        super().__init__(**kwargs)
        self.order_book = order_book  # The order book data source

    def render(self) -> Table:
        """Render the order book as a Rich table."""
        table = Table(title="Order Book")

        # Add columns to the table for displaying buy/sell orders
        table.add_column("Buy Orders (Price x Quantity)", justify="center", style="green", no_wrap=True)
        table.add_column("Sell Orders (Price x Quantity)", justify="center", style="red", no_wrap=True)

        # Get the top 10 buy and sell orders from the order book
        top_buy_orders, top_sell_orders = self.order_book.get_top_orders(n=10)

        # Ensure both lists are of the same length by padding with empty orders
        max_len = max(len(top_buy_orders), len(top_sell_orders))
        top_buy_orders += [None] * (max_len - len(top_buy_orders))
        top_sell_orders += [None] * (max_len - len(top_sell_orders))

        for buy, sell in zip(top_buy_orders, top_sell_orders):
            buy_text = f"{buy.price} x {buy.quantity}" if buy else ""
            sell_text = f"{sell.price} x {sell.quantity}" if sell else ""
            table.add_row(buy_text, sell_text)

        return table


class MatchedOrdersWidget(Widget):
    """Custom widget to display the summary panel."""

    def __init__(self, order_book: OrderBook, **kwargs):
        super().__init__(**kwargs)
        self.order_book = order_book  # The order book data source


    def render(self) -> Table:
        table = Table(title="Matches Summary")
        # Add columns to the table for displaying buy/sell orders
        table.add_column("Matched Orders", justify="center", style="bold yellow", no_wrap=True)

        matched_orders = self.order_book.get_latest_trades()

        for matched_order in matched_orders:
            quantity, price = matched_order
            matched = f"{price} x {quantity}" if matched_order else ""
            table.add_row(matched)

        return table

class AveragePirceWidget(Widget):
    """Custom widget to display the summary panel."""

    def __init__(self, order_book: OrderBook, **kwargs):
        super().__init__(**kwargs)
        self.order_book = order_book  # The order book data source


    def render(self) -> Table:
        table = Table(title="Market Price")
        # Add columns to the table for displaying buy/sell orders
        table.add_column("Market Price", justify="center", style="blue", no_wrap=True)

        avg_price = self.order_book.get_average_price()
        a_price = f"{avg_price}"  if avg_price else ""
        table.add_row(a_price)

        return table


class OrderBookApp(App):
    """A Textual app to manage order books and forms."""
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "placeholder.tcss"

    def __init__(self, order_book: OrderBook, **kwargs):
        super().__init__(**kwargs)
        self.order_book = order_book

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        
        # Create the order book widget
        self.order_book_widget = OrderBookWidget(order_book=self.order_book, id="order_book_widget")
        
        # Create the form widget and pass the order book widget reference to it
        self.market_matches = MatchedOrdersWidget( order_book=self.order_book, id="market_matches")

        self.a_price_table = AveragePirceWidget( order_book=self.order_book, id="priceWidget")

        yield Header()
    
        yield Container(
                self.order_book_widget,
                id="order_book_widget",
                classes="box1"
            )
        yield Container(
                self.market_matches,
                id="market_matches",
                classes="box"
            )
        yield Container(
                self.a_price_table,
                id="priceWidget",
                classes="box"
            )
        yield Footer()

 

    async def on_mount(self) -> None:
        """Start background task to refresh the order book widget and the summary panel."""
        async def refresh_widgets():
            # Refresh the order book widget and the summary panel
            self.order_book_widget.refresh()
            self.market_matches.refresh()  # No layout argument passed
            self.a_price_table.refresh()

        # Set an interval to call `refresh_widgets` every second
        self.set_interval(1, refresh_widgets)



# Example usage
if __name__ == "__main__":
    order_book = OrderBook()

    # Create and start a thread for alternating order generation
    order_thread = threading.Thread(target=alternating_order_generator, args=(order_book, 0.5), daemon=True)
    order_thread.start()

    # Run the app with the order book
    app = OrderBookApp(order_book=order_book)
    app.run()

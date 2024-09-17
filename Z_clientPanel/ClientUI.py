from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, Button, Select, RadioButton, RadioSet
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class OrderBookWidget(Widget):
    """Custom widget to display the order book using Rich's table."""

    # Reactive order book structure containing orders with price, quantity, and type
    order_book = reactive({"sell": [], "buy": []})

    def add_order(self, order_type: str, price: str, quantity: str, is_buy: bool) -> None:
        """Add a new order to the order book and trigger reactivity."""
        order_entry = {"price": price, "quantity": quantity, "type": order_type}

        # Append to the appropriate side (buy or sell)
        if is_buy:
            updated_buy_orders = self.order_book["buy"] + [order_entry]
            self.order_book = {"buy": updated_buy_orders, "sell": self.order_book["sell"]}
        else:
            updated_sell_orders = self.order_book["sell"] + [order_entry]
            self.order_book = {"buy": self.order_book["buy"], "sell": updated_sell_orders}

    def render(self) -> Table:
        """Render the order book as a Rich table."""
        table = Table(title="Order Book")

        # Add columns to the table for displaying buy/sell orders
        table.add_column("Buy Orders (Price x Quantity)", justify="center", style="green", no_wrap=True)
        table.add_column("Sell Orders (Price x Quantity)", justify="center", style="red", no_wrap=True)

        # Make sure both buy and sell orders lists are the same size
        max_len = max(len(self.order_book["buy"]), len(self.order_book["sell"]))

        # Fill with empty orders to balance rows if needed
        buy_orders = self.order_book["buy"] + [{"price": "", "quantity": "", "type": ""}] * (max_len - len(self.order_book["buy"]))
        sell_orders = self.order_book["sell"] + [{"price": "", "quantity": "", "type": ""}] * (max_len - len(self.order_book["sell"]))

        for buy, sell in zip(buy_orders, sell_orders):
            buy_text = f"{buy['price']} x {buy['quantity']}" if buy["price"] else ""
            sell_text = f"{sell['price']} x {sell['quantity']}" if sell["price"] else ""
            
            table.add_row(buy_text, sell_text)

        return table

class OrderFormWidget(Widget):
    """Custom widget for the order form."""
    
    def __init__(self, order_book_widget: OrderBookWidget, **kwargs):
        """Initialize the form with a reference to the order book widget."""
        super().__init__(**kwargs)
        self.order_book_widget = order_book_widget  # Keep a reference to the order book widget
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label("Enter Order"),
            Input(placeholder="Enter price", id="price_input"),
            Label("Quantity:"),
            Input(placeholder="Enter quantity", id="quantity_input"),
            Label("Order Type:"),
            Select(options=[("market", "Market Order"), ("limit", "Limit Order")], id="order_type_select"),
            Label("Buy or Sell:"),
            RadioSet(
                RadioButton("Buy", id="buy_radio", value=True),
                RadioButton("Sell", id="sell_radio"),
                id="buy_sell_radio",
            ),
            Button("Submit Order", id="submit_order"),
            id="form_container"
        )

    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle manual order submission."""
        if event.button.id == "submit_order":
            # Get form values
            price = self.query_one("#price_input", Input).value
            quantity = self.query_one("#quantity_input", Input).value
            order_type = self.query_one("#order_type_select", Select).value
            is_buy = self.query_one("#buy_radio", RadioButton).value

            # Validate input
            if not price or not quantity or not order_type:
                self.bell()  # Emit a beep sound if input is missing
                return

            # Add the order to the order book
            self.order_book_widget.add_order(order_type, price, quantity, is_buy)

            # Clear the input fields after submission
            self.query_one("#price_input", Input).value = ""
            self.query_one("#quantity_input", Input).value = ""


class OrderBookApp(App):
    """A Textual app to manage order books and forms."""
    CSS_PATH = "layout.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        
        # Create the order book widget
        self.order_book_widget = OrderBookWidget(id="order_book_widget")
        
        # Create the form widget and pass the order book widget reference to it
        self.form_widget = OrderFormWidget(order_book_widget=self.order_book_widget, id="form_widget")
        
        yield Header()
    
        yield Horizontal(
            Vertical(
                self.order_book_widget,
                id="order_book_container",
                classes="column",
            ),
            Vertical(
                self.form_widget,
                classes="column"
            ),
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = OrderBookApp()
    app.run()

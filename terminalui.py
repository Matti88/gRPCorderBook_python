from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Button, Static, Select, RadioButton, RadioSet
from textual.reactive import reactive
from textual.widget import Widget
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from textual_plotext import PlotextPlot  # Import the Plotext widget


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
            # Create a new dictionary to trigger reactivity
            self.order_book = {"buy": updated_buy_orders, "sell": self.order_book["sell"]}
        else:
            updated_sell_orders = self.order_book["sell"] + [order_entry]
            # Create a new dictionary to trigger reactivity
            self.order_book = {"buy": self.order_book["buy"], "sell": updated_sell_orders}

    def render(self) -> Panel:
        """Render the order book as a Rich table."""
        table = Table(title="Order Book")

        # Add columns to the table for displaying buy/sell orders and their type
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

        return Panel(table)


class OrderBookApp(App):
    """Main app to manage the order book and the order entry form."""

    def compose(self) -> ComposeResult:
        # Custom widget for the order book (left side)
        self.order_book_widget = OrderBookWidget(id="order_book_widget")

        # Plotext widget to display a scatter plot (right side)
        self.plotext_widget = PlotextPlot(id="plotext_widget")

        # Order form (right side)
        yield Horizontal(
            Vertical(
                Static(Text("Order Book", style="bold underline")),
                self.order_book_widget,
                id="order_book_container",
            ),
            Vertical(
                Static(Text("Enter Order", style="bold underline")),
                Static("Price:"),
                Input(placeholder="Enter price", id="price_input"),
                Static("Quantity:"),
                Input(placeholder="Enter quantity", id="quantity_input"),
                Static("Order Type:"),
                Select(options=[("market", "Market Order"), ("limit", "Limit Order")], id="order_type_select"),
                Static("Buy or Sell:"),
                RadioSet(
                    RadioButton("Buy", id="buy_radio", value=True),
                    RadioButton("Sell", id="sell_radio"),
                    id="buy_sell_radio",
                ),
                Button("Submit Order", id="submit_order"),
                id="order_form_container"
            ),
            # Add the Plotext widget in the layout for chart display
            Vertical(
                Static(Text("Chart of Sin Wave", style="bold underline")),
                self.plotext_widget,
                id="plotext_container",
            ),
        )

    def on_mount(self) -> None:
        """Set up the plot."""
        plt = self.query_one(PlotextPlot).plt
        plt.title("Sine Wave Scatter Plot")
        plt.scatter(plt.sin())

    def on_button_pressed(self, event: Button.Pressed) -> None:
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

            # Add the order to the order book via the widget
            self.order_book_widget.add_order(order_type, price, quantity, is_buy)

            # Clear the input fields after submission
            self.query_one("#price_input", Input).value = ""
            self.query_one("#quantity_input", Input).value = ""


if __name__ == "__main__":
    OrderBookApp().run()

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from time import sleep
from threading import Thread
import random

# Create a console for output
console = Console()

# Sample order book data (lists of dictionaries)
order_book = {
    "buy": [],
    "sell": []
}

# Function to display the order book in real-time
def display_order_book():
    table = Table(title="Order Book")

    # Add columns to the table for displaying the buy/sell orders
    table.add_column("Buy Orders (Price x Quantity)", justify="center", style="green", no_wrap=True)
    table.add_column("Sell Orders (Price x Quantity)", justify="center", style="red", no_wrap=True)

    # Make sure both buy and sell orders lists are the same size
    max_len = max(len(order_book["buy"]), len(order_book["sell"]))
    
    buy_orders = order_book["buy"] + [{'price': '', 'quantity': ''}] * (max_len - len(order_book["buy"]))
    sell_orders = order_book["sell"] + [{'price': '', 'quantity': ''}] * (max_len - len(order_book["sell"]))

    buy_orders  = buy_orders[0:10]
    sell_orders = sell_orders[0:10]

    for buy, sell in zip(buy_orders, sell_orders):
        buy_text = f"{buy['price']} x {buy['quantity']}" if buy['price'] else ""
        sell_text = f"{sell['price']} x {sell['quantity']}" if sell['price'] else ""
        table.add_row(buy_text, sell_text)
    
    return Panel(table)

# Function to process buy and sell orders
def process_order(order_type, price, quantity, order_kind):
    # Create the order dictionary
    order = {"price": price, "quantity": quantity, "type": order_kind}
    
    # Add to buy or sell list based on order type
    if order_type == 'buy':
        order_book["buy"].append(order)
        order_book["buy"].sort(key=lambda x: -x['price'])  # Sort by highest price for buy orders
    elif order_type == 'sell':
        order_book["sell"].append(order)
        order_book["sell"].sort(key=lambda x: x['price'])  # Sort by lowest price for sell orders

# Simulated fake order generator
def fake_order_generator():
    while True:
        # Randomly choose between buy and sell orders
        order_type = random.choice(["buy", "sell"])
        
        # Generate random price and quantity
        price = round(random.uniform(90, 110), 2)  # Price between 90 and 110
        quantity = random.randint(1, 10)  # Quantity between 1 and 10
        order_kind = random.choice(["market", "limit"])

        # Process the generated order
        process_order(order_type, price, quantity, order_kind)

        # Wait for a short random time before generating the next order
        sleep(random.uniform(1, 3))

# User input function to create manual orders
def manual_order_input():
    while True:
        console.print("\n[bold]Order Input[/bold]", style="bold cyan")
        
        # Order type (buy or sell)
        order_type = Prompt.ask("[bold green]Enter order type (buy/sell):").lower()
        if order_type not in ["buy", "sell"]:
            console.print("Invalid order type! Please enter 'buy' or 'sell'.", style="bold red")
            continue

        # Order kind (market or limit)
        order_kind = Prompt.ask("[bold green]Enter order kind (market/limit):").lower()
        if order_kind not in ["market", "limit"]:
            console.print("Invalid order kind! Please enter 'market' or 'limit'.", style="bold red")
            continue

        # If it's a limit order, ask for the price
        if order_kind == 'limit':
            try:
                price = float(Prompt.ask("[bold green]Enter limit price:"))
            except ValueError:
                console.print("Invalid price! Please enter a valid number.", style="bold red")
                continue
        else:
            # Market order doesn't require price, use 0
            price = 0

        # Order quantity
        try:
            quantity = int(Prompt.ask("[bold green]Enter quantity:"))
        except ValueError:
            console.print("Invalid quantity! Please enter a valid number.", style="bold red")
            continue

        # Confirm and commit the order
        commit = Prompt.ask(f"[bold cyan]Do you want to commit the {order_type} {order_kind} order of {quantity} units?", choices=["yes", "no"], default="yes")
        if commit == "yes":
            process_order(order_type, price, quantity, order_kind)
            console.print("[green]Order committed successfully![/green]\n")

        sleep(1)

# Function to simulate the terminal UI for the order book system
def order_book_ui():
    # Start a thread to continuously generate fake orders
    fake_order_thread = Thread(target=fake_order_generator, daemon=True)
    fake_order_thread.start()

    # Start a thread for manual input orders
    manual_order_thread = Thread(target=manual_order_input, daemon=True)
    manual_order_thread.start()

    # Create a Live object to display the order book
    with Live(display_order_book(), refresh_per_second=2) as live:
        while True:
            # Continuously refresh the display with the updated order book
            live.update(display_order_book())
            sleep(0.5)

if __name__ == "__main__":
    order_book_ui()

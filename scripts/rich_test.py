from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import track
from rich.live import Live
from rich.layout import Layout
from time import sleep

console = Console()

# Basic formatting
console.print("[bold red]Rich Features Demo[/bold red]")
console.print("=" * 50)

# Create a fancy table
table = Table(title="Rich Features Demo")
table.add_column("Feature", style="cyan")
table.add_column("Description", style="magenta")
table.add_row("Formatting", "Colors and styles")
table.add_row("Tables", "Structured data display")
table.add_row("Panels", "Boxed content")

# Print the table
console.print(table)

# Create a panel
console.print(Panel.fit("This text is in a panel!", title="Panel Demo"))

# Show some syntax highlighting


# Progress bar demo
console.print("\n[yellow]Progress Bar Demo:[/yellow]")
for step in track(range(5), description="Processing..."):
    sleep(0.2)

# Final flourish
console.print("\n[bold green]✨ Demo Complete! ✨[/bold green]")
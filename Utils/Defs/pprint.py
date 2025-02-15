from rich.console import Console
from rich.style import Style
from functools import partial

console = Console()
base_style = Style(color="#76B900", bold=True)
pprint = partial(console.print, style=base_style)
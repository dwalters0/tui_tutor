from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.text import Text
from rich.markdown import Markdown
import time


console = Console()


def stream_panel(input_text,title):
    text = ""

    with Live("", console=console, refresh_per_second=20) as live:
        for char in input_text:
            text += char
            live.update(Markdown(text))
            time.sleep(0.03)
    time.sleep(0.05)

# def stream_panel(input_text,title):
#
#     display_panel = Panel(Text(""), title=title)
#     live = Live(display_panel,
#         console=console,
#         refresh_per_second=10)
#     text = ""
#     for char in input_text:
#         text += char
#         display_panel.renderable = Text(char)
#         live.update(display_panel)
#         time.sleep(0.03)
#
#     #display_panel.renderable = ""
#     #live.update(display_panel)
#     live.stop()





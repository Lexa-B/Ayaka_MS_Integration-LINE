from langchain.schema.runnable import RunnableLambda
from functools import partial
from rich.console import Console
from rich.style import Style
from functools import partial
from Utils.Defs.pprint import pprint

def RPrint(preface=""):
    """Simple passthrough "prints, then returns" chain"""
    def print_and_return(x, preface):
        if preface: print("\n\n" + "\033[1m" + "\033[35m" + preface + "\033[0m", end="")
        pprint(x)
        return x
    return RunnableLambda(partial(print_and_return, preface=preface))

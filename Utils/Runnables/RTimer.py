from Utils.Classes.Timer import Timer
from langchain.schema.runnable import RunnableLambda

def RTimer(func):
    """Timing wrapper that returns a runnable that times the execution of the provided function"""
    def timed_execution(x):
        with Timer():
            if hasattr(func, 'invoke'):
                return func.invoke(x)
            return func(x)
    return RunnableLambda(timed_execution)

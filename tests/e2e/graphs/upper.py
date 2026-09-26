"""Test graph: proves that a module in GRAPHS_DIR is loaded; answers in upper case."""
from typing import TypedDict

from langgraph.graph import END, StateGraph

name = "upper"
description = "Returns the message in upper case."


class State(TypedDict):
    message: str
    response: str


def shout(state: State) -> State:
    return {"message": state["message"], "response": state["message"].upper()}


builder = StateGraph(State)
builder.add_node("shout", shout)
builder.set_entry_point("shout")
builder.add_edge("shout", END)
graph = builder.compile()

import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph


name = "echo"
description = "Simple echo graph that returns the user message via an LLM."


class State(TypedDict):
    message: str
    response: str


_llm = ChatOpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL"),
    api_key=os.environ.get("OPENAI_API_KEY", ""),
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
)


def chat_node(state: State) -> State:
    result = _llm.invoke(state["message"])
    return {"message": state["message"], "response": result.content}


builder = StateGraph(State)
builder.add_node("chat", chat_node)
builder.set_entry_point("chat")
builder.add_edge("chat", END)
graph = builder.compile()

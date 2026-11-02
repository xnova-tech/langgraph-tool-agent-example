"""Минимальный граф с реальным ToolNode и заранее заданными решениями."""

from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


@tool
def get_status(service: str) -> str:
    """Прочитать учебный HTTP-статус сервиса по его имени."""
    if service not in {"api", "worker"}:
        raise ValueError("service not allowed")
    return {"api": "HTTP 503", "worker": "HTTP 200"}[service]


@tool
def get_runbook(service: str) -> str:
    """Прочитать учебную инструкцию по диагностике API."""
    if service != "api":
        raise ValueError("service not allowed")
    return "проверить журнал и upstream"


def scripted_decision(messages: list) -> AIMessage:
    """Тестовый выбор следующего шага; это не языковая модель."""
    results = [m for m in messages if isinstance(m, ToolMessage)]
    if not results:
        return AIMessage(
            content="",
            tool_calls=[{"name": "get_status", "args": {"service": "api"}, "id": "call-status"}],
        )
    last = results[-1]
    if last.name == "get_status" and last.content == "HTTP 503":
        return AIMessage(
            content="",
            tool_calls=[{"name": "get_runbook", "args": {"service": "api"}, "id": "call-guide"}],
        )
    if last.name == "get_status":
        return AIMessage(content="Сервис ответил; дополнительные проверки не запрошены.")
    return AIMessage(content=f"HTTP 503; следующий шаг: {last.content}.")


def build_graph(decide: Callable[[list], AIMessage] = scripted_decision):
    """Собрать граф; вместо decide можно передать адаптер реальной LLM."""

    def model_node(state: MessagesState) -> dict:
        return {"messages": [decide(state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("model", model_node)
    builder.add_node("tools", ToolNode([get_status, get_runbook], handle_tool_errors=True))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition)
    builder.add_edge("tools", "model")
    return builder.compile()


def main() -> None:
    result = build_graph().invoke(
        {"messages": [HumanMessage(content="Что проверить у api?")]},
        config={"recursion_limit": 12},
    )
    for item in result["messages"]:
        if isinstance(item, ToolMessage):
            print(f"{item.name} -> {item.content}")
    print("completed: " + result["messages"][-1].content)


if __name__ == "__main__":
    main()

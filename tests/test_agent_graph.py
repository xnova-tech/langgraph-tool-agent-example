"""Контракт маршрута LangGraph и ошибок ToolNode."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError

from agent_graph import build_graph, get_runbook, get_status


def ask(decide=None, limit=12):
    graph = build_graph() if decide is None else build_graph(decide)
    return graph.invoke(
        {"messages": [HumanMessage(content="Что проверить у api?")]},
        config={"recursion_limit": limit},
    )["messages"]


def call(name, service="api"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": {"service": service}, "id": "call-1"}])


def test_two_tool_messages_and_finish():
    messages = ask()
    results = [message for message in messages if isinstance(message, ToolMessage)]
    assert [(message.name, message.content) for message in results] == [
        ("get_status", "HTTP 503"),
        ("get_runbook", "проверить журнал и upstream"),
    ]
    assert messages[-1].content == "HTTP 503; следующий шаг: проверить журнал и upstream."


def test_no_tool_call_finishes_without_tool_message():
    messages = ask(lambda _: AIMessage(content="Без дополнительных проверок."))
    assert len(messages) == 2
    assert not any(isinstance(message, ToolMessage) for message in messages)


def test_unknown_tool_returns_error_message():
    counter = iter([call("not_available"), AIMessage(content="Остановка.")])
    messages = ask(lambda _: next(counter))
    errors = [message for message in messages if isinstance(message, ToolMessage)]
    assert len(errors) == 1
    assert errors[0].status == "error"


def test_bad_service_does_not_return_status():
    counter = iter([call("get_status", "../../secret"), AIMessage(content="Остановка.")])
    messages = ask(lambda _: next(counter))
    errors = [message for message in messages if isinstance(message, ToolMessage)]
    assert len(errors) == 1
    assert errors[0].status == "error"
    assert errors[0].content != "HTTP 503"


def test_recursion_limit_stops_loop():
    with pytest.raises(GraphRecursionError):
        ask(lambda _: call("get_status"), limit=3)


def test_read_only_functions_reject_other_services():
    assert get_status.invoke({"service": "worker"}) == "HTTP 200"
    with pytest.raises(ValueError):
        get_status.invoke({"service": "other"})
    with pytest.raises(ValueError):
        get_runbook.invoke({"service": "worker"})

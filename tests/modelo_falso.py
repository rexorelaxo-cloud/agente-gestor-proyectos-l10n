"""LLM simulado SOLO para tests offline: permite verificar la mecánica del grafo
(ciclo, persistencia, thread_id, recursion_limit) sin API key. No reemplaza al LLM real."""
from __future__ import annotations

import json
import uuid
from typing import Any, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

Politica = Callable[[list[BaseMessage]], AIMessage]


def llamar(*llamadas: tuple[str, dict[str, Any]]) -> AIMessage:
    return AIMessage(content="", tool_calls=[
        {"name": n, "args": a, "id": uuid.uuid4().hex[:8], "type": "tool_call"} for n, a in llamadas])


def turno_actual(msgs: list[BaseMessage]) -> list[BaseMessage]:
    ultimo = max(i for i, m in enumerate(msgs) if isinstance(m, HumanMessage))
    return msgs[ultimo:]


class ModeloFalso(BaseChatModel):
    politica: Any = None
    vistos: list[list[BaseMessage]] = []  # mensajes recibidos en cada invocación

    @property
    def _llm_type(self) -> str:
        return "falso"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ModeloFalso":
        return self

    def _generate(self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kw: Any) -> ChatResult:
        self.vistos.append(list(messages))
        return ChatResult(generations=[ChatGeneration(message=self.politica(list(messages)))])


def tool_results(msgs: list[BaseMessage]) -> list[dict[str, Any]]:
    return [json.loads(m.content) for m in msgs if isinstance(m, ToolMessage)]

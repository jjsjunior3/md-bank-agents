import logging
import operator
import os
from typing import Annotated, TypedDict

import httpx
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from src.agents import classificar_pergunta

logger = logging.getLogger(__name__)

ABRIR_CONTA_URL = os.getenv("ABRIR_CONTA_URL", "http://abrir_conta_agent:8000/consultar")
CARTAO_CREDITO_URL = os.getenv("CARTAO_CREDITO_URL", "http://cartao_credito_agent:8000/consultar")


class SupervisorState(TypedDict):
    query: str
    respostas: Annotated[list[str], operator.add]


def _chamar_agente(url: str, query: str) -> str:
    try:
        response = httpx.post(url, json={"message": query}, timeout=60)
        if response.status_code == 200:
            return response.json().get("resposta", "Resposta não encontrada")
        return f"Erro ao consultar agente (status {response.status_code})"
    except Exception:
        logger.exception(f"Erro ao consultar agente em {url}")
        return "Erro ao consultar agente"


def node_abrir_conta(state: SupervisorState) -> dict:
    resposta = _chamar_agente(ABRIR_CONTA_URL, state["query"])
    return {"respostas": [resposta]}


def node_cartao_credito(state: SupervisorState) -> dict:
    resposta = _chamar_agente(CARTAO_CREDITO_URL, state["query"])
    return {"respostas": [resposta]}


def router(state: SupervisorState):
    agentes = classificar_pergunta(state["query"])

    destinos = []
    if "abrir_conta" in agentes:
        destinos.append(Send("abrir_conta_node", state))
    if "cartao_credito" in agentes:
        destinos.append(Send("cartao_credito_node", state))

    return destinos


builder = StateGraph(SupervisorState)
builder.add_node("abrir_conta_node", node_abrir_conta)
builder.add_node("cartao_credito_node", node_cartao_credito)
builder.add_conditional_edges(START, router, ["abrir_conta_node", "cartao_credito_node"])
builder.add_edge("abrir_conta_node", END)
builder.add_edge("cartao_credito_node", END)

grafo = builder.compile()


async def executar_supervisor(texto_usuario: str) -> str:
    resultado = grafo.invoke({"query": texto_usuario, "respostas": []})
    respostas = resultado.get("respostas", [])

    if not respostas:
        return "Não consegui entender sua solicitação"

    return "\n\n".join(respostas)
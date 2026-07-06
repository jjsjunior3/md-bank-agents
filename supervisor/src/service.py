import logging
import operator
import uuid
from typing import Annotated, TypedDict

import httpx
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, Role, TextPart

from src.agents import classificar_pergunta

logger = logging.getLogger(__name__)

HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

AGENTS = {
    "cartao_credito": "http://cartao_credito_agent:8000",
    "abrir_conta": "http://abrir_conta_agent:8000",
}

CLIENT_CACHE = {}


async def request_agent(message: str, agent_url: str) -> str:
    if agent_url not in CLIENT_CACHE:
        logger.info(f"Descobrindo AgentCard em {agent_url}")

        resolver = A2ACardResolver(
            httpx_client=HTTPX_CLIENT,
            base_url=agent_url,
        )

        agent_card = await resolver.get_agent_card()
        logger.info(f"Agent encontrado: {agent_card.name}")

        config = ClientConfig(
            httpx_client=HTTPX_CLIENT,
            streaming=False,
        )
        factory = ClientFactory(config)
        CLIENT_CACHE[agent_url] = factory.create(agent_card)

    client = CLIENT_CACHE[agent_url]

    msg = Message(
        role=Role.user,
        message_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(text=message))],
    )

    logger.info(f"Enviando mensagem para agente: {message}")

    async for event in client.send_message(msg):
        if isinstance(event, Message):
            for part in event.parts:
                if part.root.kind == "text":
                    return part.root.text

    return "Sem resposta do agente."


class SupervisorState(TypedDict):
    query: str
    respostas: Annotated[list[str], operator.add]


async def node_abrir_conta(state: SupervisorState) -> dict:
    resposta = await request_agent(state["query"], AGENTS["abrir_conta"])
    return {"respostas": [resposta]}


async def node_cartao_credito(state: SupervisorState) -> dict:
    resposta = await request_agent(state["query"], AGENTS["cartao_credito"])
    return {"respostas": [resposta]}


def router(state: SupervisorState):
    agentes = classificar_pergunta(state["query"])
    logger.info(f"Agentes selecionados: {agentes}")

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
    resultado = await grafo.ainvoke({"query": texto_usuario, "respostas": []})
    respostas = resultado.get("respostas", [])

    if not respostas:
        return "Não consegui entender sua solicitação"

    return "\n\n".join(respostas)
import logging
import operator
import uuid
from typing import Annotated, AsyncGenerator, TypedDict

import httpx
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, Role, TextPart

from ag_ui.core import (
    RunAgentInput,
    EventType,
    BaseEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    StateSnapshotEvent,
)

from src.agents import classificar_pergunta

logger = logging.getLogger(__name__)

HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

BFA_URL = "http://bfa:8000"

AGENTS_FALLBACK = {
    "cartao_credito": "http://cartao_credito_agent:8000",
    "abrir_conta": "http://abrir_conta_agent:8000",
}

CLIENT_CACHE = {}
SESSION_LAST_AGENTS: dict[str, list[str]] = {}


async def resolve_via_bfa(query: str) -> dict | None:
    try:
        response = await HTTPX_CLIENT.get(f"{BFA_URL}/resolve", params={"query": query})
        if response.status_code == 200:
            return response.json()
    except Exception:
        logger.exception("Erro ao consultar o BFA, usando fallback local")
    return None


async def request_agent(message: str, agent_url: str) -> str:
    if agent_url not in CLIENT_CACHE:
        logger.info(f"Descobrindo AgentCard em {agent_url}")
        resolver = A2ACardResolver(httpx_client=HTTPX_CLIENT, base_url=agent_url)
        agent_card = await resolver.get_agent_card()
        logger.info(f"Agent encontrado: {agent_card.name}")

        config = ClientConfig(httpx_client=HTTPX_CLIENT, streaming=False)
        factory = ClientFactory(config)
        CLIENT_CACHE[agent_url] = factory.create(agent_card)

    client = CLIENT_CACHE[agent_url]

    msg = Message(
        role=Role.user,
        message_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(text=message))],
    )

    async for event in client.send_message(msg):
        if isinstance(event, Message):
            for part in event.parts:
                if part.root.kind == "text":
                    return part.root.text

    return "Sem resposta do agente."


class SupervisorState(TypedDict):
    query: str
    session_id: str
    respostas: Annotated[list[str], operator.add]


async def node_abrir_conta(state: SupervisorState) -> dict:
    resposta = await request_agent(state["query"], AGENTS_FALLBACK["abrir_conta"])
    return {"respostas": [resposta]}


async def node_cartao_credito(state: SupervisorState) -> dict:
    resposta = await request_agent(state["query"], AGENTS_FALLBACK["cartao_credito"])
    return {"respostas": [resposta]}


def router(state: SupervisorState):
    session_id = state["session_id"]
    agentes = classificar_pergunta(state["query"], thread_id=session_id)

    if not agentes:
        agentes = SESSION_LAST_AGENTS.get(session_id, [])
    else:
        SESSION_LAST_AGENTS[session_id] = agentes

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


async def executar_supervisor(texto_usuario: str, session_id: str = "default") -> str:
    resultado = await grafo.ainvoke(
        {"query": texto_usuario, "session_id": session_id, "respostas": []}
    )
    respostas = resultado.get("respostas", [])
    if not respostas:
        return "Não consegui entender sua solicitação"
    return "\n\n".join(respostas)


async def executar_supervisor_bfa(texto_usuario: str, session_id: str = "default") -> str:
    resolvido = await resolve_via_bfa(texto_usuario)

    if not resolvido or resolvido.get("type") in (None, "no_match", "no_confident_match"):
        SESSION_LAST_AGENTS.pop(session_id, None)
        return await executar_supervisor(texto_usuario, session_id)

    best = resolvido["best"]
    tipo = best["type"]
    skill_id = best["skill"]

    logger.info(f"BFA resolveu '{texto_usuario}' -> {tipo}:{skill_id} (score={best['normalized_score']:.2f})")

    if tipo == "agent":
        agent_url = best["data"]["agent_url"]
        resposta = await request_agent(texto_usuario, agent_url)
        SESSION_LAST_AGENTS[session_id] = [skill_id]
        return resposta

    if tipo == "tool":
        agentes = SESSION_LAST_AGENTS.get(session_id, ["cartao_credito"])
        respostas = []
        for agente in agentes:
            if agente in AGENTS_FALLBACK:
                resposta = await request_agent(texto_usuario, AGENTS_FALLBACK[agente])
                respostas.append(resposta)
        return "\n\n".join(respostas) if respostas else "Não consegui processar sua solicitação."

    return await executar_supervisor(texto_usuario, session_id)


async def executar_supervisor_stream(input_data: RunAgentInput) -> AsyncGenerator[BaseEvent, None]:
    session_id = input_data.thread_id
    assistant_id = str(uuid.uuid4())

    user_messages = [m for m in input_data.messages if m.role == "user"]
    user_message = user_messages[-1].content if user_messages else ""

    state = {"agentes": [], "respostas": []}

    yield TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START,
        message_id=assistant_id,
        role="assistant",
    )

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta="Analisando sua solicitação...\n\n",
    )

    agentes = classificar_pergunta(user_message, thread_id=session_id)

    if not agentes:
        agentes = SESSION_LAST_AGENTS.get(session_id, [])
    else:
        SESSION_LAST_AGENTS[session_id] = agentes

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Agentes selecionados: {', '.join(agentes)}\n\n",
    )

    state["agentes"] = agentes
    yield StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=state)

    respostas = []
    for agent_name in agentes:
        if agent_name not in AGENTS_FALLBACK:
            continue

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"Chamando agente: {agent_name}...\n",
        )

        resposta = await request_agent(user_message, AGENTS_FALLBACK[agent_name])
        respostas.append(resposta)

        yield TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=assistant_id,
            delta=f"{agent_name} respondeu\n\n",
        )

        state["respostas"].append({agent_name: resposta})
        yield StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=state)

    resposta_final = "\n\n".join(respostas) if respostas else "Não consegui entender sua solicitação"

    yield TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=assistant_id,
        delta=f"Resultado final:\n\n{resposta_final}",
    )

    yield TextMessageEndEvent(
        type=EventType.TEXT_MESSAGE_END,
        message_id=assistant_id,
    )
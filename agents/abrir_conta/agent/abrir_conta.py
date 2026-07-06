import os
import asyncio
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

_llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
)

agente_abertura_conta = create_agent(
    _llm,
    tools=[],
    system_prompt=(
        "Você é um especialista em abertura de contas do banco MDBank. "
        "Ajude o cliente a abrir uma conta e explique os tipos disponíveis."
    ),
)


def _invoke(mensagem: str) -> str:
    resultado = agente_abertura_conta.invoke(
        {"messages": [HumanMessage(content=mensagem)]}
    )
    mensagem_ia = resultado["messages"][-1]
    return str(mensagem_ia.content)


async def run_agent(mensagem: str) -> str:
    return await asyncio.to_thread(_invoke, mensagem)
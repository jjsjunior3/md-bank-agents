import os
import asyncio
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

_llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.3,
)

client = MultiServerMCPClient(
    {
        "conta": {
            "transport": "http",
            "url": "http://recursos:8000/mcp_gateway",
        }
    }
)

memory = InMemorySaver()

agent = None


async def build_agent():
    tools = await client.get_tools()

    agente = create_agent(
        _llm,
        tools=tools,
        system_prompt=(
            "Você é um assistente do MDBank.\n\n"
            "Você deve SEMPRE usar tools para decisões reais.\n\n"
            "Fluxo obrigatório:\n"
            "1. Se cliente pedir cartão:\n"
            "   - Use consultar_conta\n"
            "   - Se não existir:\n"
            "       → informe o problema\n"
            "       → ofereça abrir conta\n\n"
            "2. Para abrir conta:\n"
            "   - Use gerar_prompt_abertura\n"
            "   - Depois criar_ou_buscar_conta\n\n"
            "3. Após conta criada:\n"
            "   - Use solicitar_cartao\n\n"
            "Regras:\n"
            "- Nunca invente dados\n"
            "- Sempre use tools\n"
            "- Use mensagens claras para o cliente\n"
        ),
        checkpointer=memory,
    )
    return agente


async def run_agent(mensagem: str, thread_id: str = "1") -> str:
    global agent

    if not agent:
        agent = await build_agent()

    resultado = await agent.ainvoke(
        {"messages": [HumanMessage(content=mensagem)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return resultado["messages"][-1].content
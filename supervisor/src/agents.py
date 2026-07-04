from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Usando OpenRouter (Gemini 2.5 Flash) para manter o custo baixo durante o estudo,
# seguindo o mesmo padrão já usado no projeto langgraph-agents.
__llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
)

agente_cartao_credito = create_agent(
    __llm,
    tools=[],
    system_prompt=(
        "Você é um especialista em cartão de crédito do banco MDBank. "
        "Ajude o cliente com dúvidas, solicitação e limites."
    ),
)

agente_abertura_conta = create_agent(
    __llm,
    tools=[],
    system_prompt=(
        "Você é um especialista em abertura de contas do banco MDBank. "
        "Ajude o cliente a abrir uma conta e explique os tipos disponíveis."
    ),
)


def classificar_pergunta(pergunta: str) -> str:
    prompt = f"""
    Classifique a intenção do usuário.

    Possíveis agentes:
    cartao_credito
    abrir_conta

    Pergunta: {pergunta}

    Responda apenas com o nome do agente.
    """
    resposta = __llm.invoke(prompt)
    return str(resposta.content).strip()


async def executar_supervisor(texto_usuario: str) -> str:
    agente = classificar_pergunta(texto_usuario)

    if agente == "cartao_credito":
        resultado = agente_cartao_credito.invoke(
            {"messages": [HumanMessage(content=texto_usuario)]}
        )
    elif agente == "abrir_conta":
        resultado = agente_abertura_conta.invoke(
            {"messages": [HumanMessage(content=texto_usuario)]}
        )
    else:
        return "Não consegui entender sua solicitação"

    mensagem_ia = resultado["messages"][-1]
    return str(mensagem_ia.content)
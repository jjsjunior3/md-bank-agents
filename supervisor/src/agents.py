import logging
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)


class ClassificacaoIntencao(BaseModel):
    agentes: list[str] = Field(
        description=(
            "Lista dos agentes que devem atender o cliente. "
            "Valores possíveis: 'cartao_credito', 'abrir_conta'. "
            "Pode conter um ou os dois valores, dependendo da necessidade do cliente."
        )
    )


parser = JsonOutputParser(pydantic_object=ClassificacaoIntencao)

prompt = PromptTemplate(
    template=(
        "Classifique a intenção do usuário.\n\n"
        "Possíveis agentes:\n"
        "- cartao_credito\n"
        "- abrir_conta\n\n"
        "O cliente pode precisar de um ou dos dois agentes na mesma mensagem.\n\n"
        "Pergunta: {pergunta}\n\n"
        "{format_instructions}"
    ),
    input_variables=["pergunta"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

classificador = prompt | llm | parser

# Memória do próprio classificador/roteador — o supervisor também "lembra"
# do contexto da conversa, não só os agentes de domínio.
router_memory = InMemorySaver()

router_agent = create_agent(
    llm,
    tools=[],
    system_prompt="Você ajuda a manter contexto de conversas bancárias do MDBank.",
    checkpointer=router_memory,
)


def classificar_pergunta(pergunta: str, thread_id: str = "1") -> list[str]:
    resultado = classificador.invoke({"pergunta": pergunta})
    agentes = resultado.get("agentes", [])
    logger.info(f"Agentes selecionados: {agentes}")

    # Mantém o router_agent "ciente" da conversa (mesmo padrão de thread_id
    # usado pelos agentes de domínio), preparando terreno para features futuras
    # que dependam desse contexto compartilhado.
    router_agent.invoke(
        {"messages": [HumanMessage(content=pergunta)]},
        {"configurable": {"thread_id": thread_id}},
    )

    return agentes
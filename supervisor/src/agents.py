import logging
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
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


def classificar_pergunta(pergunta: str) -> list[str]:
    resultado = classificador.invoke({"pergunta": pergunta})
    agentes = resultado.get("agentes", [])
    logger.info(f"Agentes selecionados: {agentes}")
    return agentes
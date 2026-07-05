import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
)

agente_cartao_credito = create_agent(
    llm,
    tools=[],
    system_prompt=(
        "Você é um especialista em cartão de crédito do banco MDBank. "
        "Ajude o cliente com dúvidas, solicitação e limites."
    ),
)


class AgentRequest(BaseModel):
    message: str


@app.post("/consultar")
async def consultar(payload: AgentRequest):
    try:
        logger.info(f"[cartao_credito_agent] Mensagem recebida: {payload.message}")
        resultado = agente_cartao_credito.invoke(
            {"messages": [HumanMessage(content=payload.message)]}
        )
        mensagem_ia = resultado["messages"][-1]
        resposta = str(mensagem_ia.content)
        logger.info(f"[cartao_credito_agent] Resposta gerada: {resposta}")
        return {"resposta": resposta}
    except Exception as e:
        logger.exception("[cartao_credito_agent] Erro ao processar requisição")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "cartao_credito"}
import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from executor import CartaoCreditoExecutor

logging.basicConfig(level=logging.INFO)

skill = AgentSkill(
    id="cartao_credito",
    name="Cartão de Crédito MDBank",
    description="Ajuda clientes com dúvidas, solicitação e limites de cartão de crédito.",
    tags=[
        "cartao de credito",
        "solicitar cartao",
        "limite",
        "fatura",
        "cartao platinum",
        "cartao gold",
    ],
    examples=[
        "quero solicitar um cartão de crédito",
        "qual o limite do meu cartão?",
        "quero um cartão Platinum",
        "quais cartões vocês oferecem?",
    ],
)

agent_card = AgentCard(
    name="Agente de Cartão de Crédito MDBank",
    description="Especialista em cartão de crédito do MDBank.",
    url="http://cartao_credito_agent:8000/",
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[skill],
    version="1.0.0",
    capabilities=AgentCapabilities(),
)

handler = DefaultRequestHandler(
    agent_executor=CartaoCreditoExecutor(),
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(
    http_handler=handler,
    agent_card=agent_card,
)

app = server.build()
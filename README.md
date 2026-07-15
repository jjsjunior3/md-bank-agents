# MD Bank — Multi-Agent Banking Assistant

A production-style multi-agent banking system built to study and apply modern AI agent protocols in practice: **A2A** (Agent-to-Agent), **MCP** (Model Context Protocol), and **AG-UI** (Agent-User Interaction Protocol).

Instead of a single monolithic chatbot, MD Bank is composed of independent, containerized agents that discover each other, share tools through a standardized protocol, and stream their reasoning live to a React front-end.

> This project was built as a hands-on companion to a course on agent protocols, then extended, debugged, and hardened beyond the course material — including fixing real dependency/version issues and protocol mismatches discovered by testing against the actual published packages rather than trusting course transcripts blindly.

---

## Why this project exists

Most "AI chatbot" tutorials stop at a single LLM call wrapped in a prompt. MD Bank goes further: it explores how real agent systems are architected once you need **multiple specialized domains**, **inter-agent communication**, **shared tools**, and **a UI that reacts to agent state in real time** — the same class of problems production agent platforms (like AWS Bedrock AgentCore) solve as managed services.

## Architecture overview

```
┌─────────────────┐        ┌─────────────────┐
│  Streamlit UI    │        │   React + AG-UI  │
│  (simple chat)    │        │ (streaming state) │
└─────────┬────────┘        └────────┬─────────┘
          │  POST /chat              │  POST / (SSE)
          └────────────┬─────────────┘
                        ▼
              ┌───────────────────┐
              │     Supervisor      │
              │  (LangGraph router)  │
              │  - intent classifier │
              │  - session memory    │
              └─────────┬─────────┘
                        │  A2A protocol
          ┌─────────────┴─────────────┐
          ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ Account Agent      │        │ Credit Card Agent  │
│ (A2A server)        │        │ (A2A server)         │
│ LangChain + memory   │        │ LangChain + memory    │
└─────────┬─────────┘        └─────────┬─────────┘
          │           MCP protocol           │
          └─────────────┬─────────────┘
                        ▼
              ┌───────────────────┐
              │      Resources      │
              │   (FastMCP server)   │
              │ tools / resources /   │
              │ prompts (account DB)  │
              └───────────────────┘
```

Every box above is an **independent Docker container**. Agents don't share memory or import each other's code — they only know how to speak the protocol.

## Protocols in practice

| Protocol | Role | Where it lives |
|---|---|---|
| **A2A** | Agent discovery & agent-to-agent communication over HTTP/JSON-RPC. The Supervisor never hardcodes agent logic — it resolves each agent's `AgentCard`, caches the client, and sends structured messages. | `supervisor/src/service.py`, `agents/*/server.py` |
| **MCP** | Exposes structured tools, resources, and prompts to agents. Domain agents connect to the `recursos` server via `MultiServerMCPClient` and consume tools like `criar_ou_buscar_conta` or `solicitar_cartao` — the LLM never invents banking data, it always calls a tool. | `recursos/app.py`, `agents/*/agent/*.py` |
| **AG-UI** | Streams agent execution as typed SSE events (`TEXT_MESSAGE_START/CONTENT/END`, `STATE_SNAPSHOT`, `RUN_FINISHED`) so the front-end can render live "thinking" state, not just a final answer. | `supervisor/app.py` (`/` route), `frontend2/src/ChatPage.jsx` |

### Design decisions worth noting

- **Routing over sub-agents**: the Supervisor classifies intent and routes to isolated domain agents (account, credit card) instead of a single agent trying to handle every banking topic — keeps prompts focused and avoids context pollution.
- **Parallel execution**: when a user asks for two things at once ("open an account and request a card"), the router dispatches both agents concurrently via LangGraph's `Send`, and responses are merged.
- **Sticky session routing**: if a follow-up message has no clear intent (e.g. the user just types a CPF), the Supervisor falls back to the last agent used in that session instead of failing.
- **Tools vs. Resources**: strict separation between *actions/mutations* (tools, e.g. `criar_ou_buscar_conta`) and *pure reads* (resources, e.g. `conta://{cpf}`) — a core MCP design principle applied throughout.

## Tech stack

- **Orchestration**: LangGraph (`StateGraph`, `Send`, `InMemorySaver` for conversation memory)
- **Agents**: LangChain (`create_agent`) + Google Gemini 2.5 Flash via OpenRouter
- **Protocols**: `a2a-sdk`, `fastmcp`, `ag-ui-protocol`
- **Backend**: FastAPI (Supervisor + domain agents), Starlette (A2A servers)
- **Frontend**: Streamlit (simple chat) and React + Tailwind (AG-UI streaming client)
- **Infra**: Docker Compose, one container per service

## Project structure

```
md-bank-agents/
├── docker-compose.yml
├── supervisor/          # Router + A2A client + AG-UI server
├── agents/
│   ├── abrir_conta/     # Account opening domain agent (A2A server)
│   └── cartao_credito/  # Credit card domain agent (A2A server)
├── recursos/            # MCP server (tools, resources, prompts)
├── frontend/            # Streamlit UI
└── frontend2/            # React UI (AG-UI streaming)
```

## Running locally

Requires Docker Desktop.

```bash
git clone https://github.com/jjsjunior3/md-bank-agents.git
cd md-bank-agents
cp supervisor/.env.example supervisor/.env
cp agents/abrir_conta/.env.example agents/abrir_conta/.env
cp agents/cartao_credito/.env.example agents/cartao_credito/.env
# fill in OPENROUTER_API_KEY in each .env

docker compose up --build
```

| Service | URL |
|---|---|
| Streamlit chat | http://localhost:9090 |
| React (AG-UI) chat | http://localhost:3000 |
| Supervisor API docs | http://localhost:8080/docs |
| MCP server (Insomnia/MCP client) | http://localhost:8084/mcp_gateway |

## What I'd build next

- Propagate `session_id` end-to-end into A2A `thread_id` for true per-user memory isolation (currently a known simplification, flagged in code)
- Persist checkpointer state (Redis) instead of in-memory, for multi-replica deployments
- Add a BFA (Backend For Agents) layer to centralize catalog discovery and deterministic business rules currently split across the Supervisor
- Add automated tests for the routing/classification logic

## About this project

Built by [José João Santos Júnior](https://github.com/jjsjunior3) as part of a self-directed path into AI agent engineering — combining structured coursework with production-grade practices already applied in [SynerEduc](https://github.com/jjsjunior3), a school management SaaS in active production.
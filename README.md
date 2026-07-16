# MD Bank — Multi-Agent Banking Assistant

A production-style multi-agent banking system built to study and apply modern AI agent protocols in practice: **A2A** (Agent-to-Agent), **MCP** (Model Context Protocol), **AG-UI** (Agent-User Interaction Protocol), and **BFA** (Backend For Agents).

Instead of a single monolithic chatbot, MD Bank is composed of independent, containerized agents that discover each other dynamically, share tools through a standardized protocol, stream their reasoning live to a React front-end, and are resolved at runtime through a dedicated discovery/ranking layer — no hardcoded routing.

> This project was built as a hands-on companion to a course on agent protocols, then extended, debugged, and hardened beyond the course material — including fixing real dependency/version issues and protocol mismatches discovered by testing against the actual published packages rather than trusting course transcripts blindly, and completing the course's final exercise (wiring the BFA into the Supervisor's routing).

---

## Why this project exists

Most "AI chatbot" tutorials stop at a single LLM call wrapped in a prompt. MD Bank goes further: it explores how real agent systems are architected once you need **multiple specialized domains**, **inter-agent communication**, **shared tools**, **dynamic discovery instead of hardcoded routing**, and **a UI that reacts to agent state in real time** — the same class of problems production agent platforms (like AWS Bedrock AgentCore) solve as managed services.

## Architecture overview

```
┌─────────────────┐        ┌─────────────────┐
│  Streamlit UI     │        │   React + AG-UI   │
│  (simple chat)     │        │ (streaming state)  │
└─────────┬────────┘        └────────┬─────────┘
          │  POST /chat              │  POST / (SSE)
          └────────────┬─────────────┘
                        ▼
              ┌───────────────────┐
              │     Supervisor      │
              │  (LangGraph router)  │
              │  - intent classifier │
              │  - session memory    │
              │  - BFA-aware routing │
              └─────────┬─────────┘
                    A2A  │  GET /resolve
          ┌──────────────┼──────────────┐
          ▼               ▼               ▼
┌──────────────────┐ ┌───────────┐ ┌──────────────────┐
│ Account Agent      │ │    BFA      │ │ Credit Card Agent  │
│ (A2A server)         │ │ (discovery  │ │ (A2A server)          │
│ LangChain + memory    │ │  + BM25    │ │ LangChain + memory     │
└─────────┬─────────┘ │  ranking)  │ └─────────┬─────────┘
          │            └─────┬─────┘           │
          │      MCP protocol │      MCP protocol
          └─────────────┬─────┴─────────────┘
                        ▼
              ┌───────────────────┐
              │      Resources      │
              │   (FastMCP server)   │
              │ tools / resources /   │
              │ prompts (account DB)  │
              └───────────────────┘
```

Every box above is an **independent Docker container**. Agents don't share memory or import each other's code — they only know how to speak a protocol.

## Protocols in practice

| Protocol | Role | Where it lives |
|---|---|---|
| **A2A** | Agent discovery & agent-to-agent communication over HTTP/JSON-RPC. Neither the Supervisor nor the BFA hardcode agent logic — they resolve each agent's `AgentCard`, cache the client, and send structured messages. | `supervisor/src/service.py`, `bfa/discovery.py`, `agents/*/server.py` |
| **MCP** | Exposes structured tools, resources, and prompts to agents. Domain agents connect to the `recursos` server via `MultiServerMCPClient` and consume tools like `criar_ou_buscar_conta` or `solicitar_cartao` — the LLM never invents banking data, it always calls a tool. A custom REST route (`/tools`) also exposes tool metadata for the BFA's discovery layer. | `recursos/app.py`, `agents/*/agent/*.py` |
| **AG-UI** | Streams agent execution as typed SSE events (`TEXT_MESSAGE_START/CONTENT/END`, `STATE_SNAPSHOT`, `RUN_FINISHED`) so the front-end can render live "thinking" state, not just a final answer. | `supervisor/app.py` (`/` route), `frontend2/src/ChatPage.jsx` |
| **BFA** | A dedicated discovery/ranking service that catalogs every agent (via A2A) and every tool (via MCP), then resolves a natural-language query to the best matching agent or tool using BM25 ranking with a confidence threshold. The Supervisor's `/chat-bfa` endpoint queries it instead of routing through a static dictionary — with automatic fallback to static routing if the BFA is unavailable. | `bfa/` (`discovery.py`, `mcp_discovery.py`, `registry.py`, `app.py`), `supervisor/src/service.py` (`executar_supervisor_bfa`) |

### Design decisions worth noting

- **Routing over sub-agents**: the Supervisor classifies intent and routes to isolated domain agents (account, credit card) instead of a single agent trying to handle every banking topic — keeps prompts focused and avoids context pollution.
- **Parallel execution**: when a user asks for two things at once ("open an account and request a card"), the router dispatches both agents concurrently via LangGraph's `Send`, and responses are merged.
- **Sticky session routing**: if a follow-up message has no clear intent (e.g. the user just types a CPF), the Supervisor falls back to the last agent used in that session instead of failing.
- **Tools vs. Resources**: strict separation between *actions/mutations* (tools, e.g. `criar_ou_buscar_conta`) and *pure reads* (resources, e.g. `conta://{cpf}`) — a core MCP design principle applied throughout.
- **Dynamic discovery over static config**: the BFA builds its catalog at startup by querying live agent cards and MCP tool metadata — adding a new agent or tool requires no change to the Supervisor's code, only registration in the BFA's endpoint lists.
- **Confidence-aware resolution**: the BFA's BM25 search returns a `no_confident_match` result (instead of a low-quality guess) when the top score falls below a threshold — routing decisions fail loud, not silently wrong.
- **Fallback-first integration**: `/chat-bfa` degrades gracefully to static routing if the BFA is unreachable, rather than breaking the whole conversation flow — a small but deliberate reliability pattern.

## Tech stack

- **Orchestration**: LangGraph (`StateGraph`, `Send`, `InMemorySaver` for conversation memory)
- **Agents**: LangChain (`create_agent`) + Google Gemini 2.5 Flash via OpenRouter
- **Protocols**: `a2a-sdk`, `fastmcp`, `ag-ui-protocol`
- **Discovery/Ranking**: `rank-bm25` + `numpy` (BFA's search layer)
- **Backend**: FastAPI (Supervisor, BFA, domain agents), Starlette (A2A servers)
- **Frontend**: Streamlit (simple chat) and React + Tailwind (AG-UI streaming client)
- **Infra**: Docker Compose, one container per service

## Project structure

```
md-bank-agents/
├── docker-compose.yml
├── supervisor/          # Router + A2A client + AG-UI server + BFA-aware routing
├── bfa/                 # Backend For Agents: agent/tool discovery + BM25 resolution
├── agents/
│   ├── abrir_conta/     # Account opening domain agent (A2A server)
│   └── cartao_credito/  # Credit card domain agent (A2A server)
├── recursos/            # MCP server (tools, resources, prompts)
├── frontend/             # Streamlit UI
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
| BFA discovery API | http://localhost:8083/docs |
| MCP server (Insomnia/MCP client) | http://localhost:8084/mcp_gateway |

### Trying the BFA directly

```bash
curl "http://localhost:8083/resolve?query=abrir conta"
curl "http://localhost:8083/resolve?query=como funciona o cartao de credito"
curl http://localhost:8083/agents
curl http://localhost:8083/tools
```

## What I'd build next

- Propagate `session_id` end-to-end into A2A `thread_id` for true per-user memory isolation (currently a known simplification, flagged in code)
- Persist checkpointer state (Redis) instead of in-memory, for multi-replica deployments
- Let the BFA execute tool calls directly (not just resolve them) for simple, single-step requests — currently left as an exercise, per the course
- Add automated tests for the routing/classification and BFA resolution logic
- Add authentication between agents (currently open within the Docker network — fine for a local/study project, not for real deployment)

## About this project

Built by [José João Santos Júnior](https://github.com/jjsjunior3) as part of a self-directed path into AI agent engineering — combining structured coursework with production-grade practices already applied in [SynerEduc](https://github.com/jjsjunior3), a school management SaaS in active production.
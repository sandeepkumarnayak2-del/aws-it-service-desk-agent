Architecture

Overview

The Enterprise AI Service Desk uses FastAPI as the API layer and LangGraph to orchestrate the different agents and maintain workflow state.

The system combines multi-agent routing, internal knowledge retrieval, memory, MCP-based tools, and human approval for actions that can change data.

User
  |
  v
FastAPI
  |
  +-- Authentication / Authorization
  +-- Validation / Guardrails
  +-- Rate Limiting
  |
  v
LangGraph
  |
  v
Supervisor Agent
  |
  +-- Knowledge Agent ----> Internal RAG
  |          |
  |          +-- insufficient evidence
  |                       |
  |                       v
  |                Investigation Agent
  |                       |
  |                       +-- action required
  |                                  |
  |                                  v
  |                            Action Agent
  |
  +-- Ticket Agent -------> MCP -------> Ticket Tools
  |
  +-- General Agent
  |
  +-- Action Agent -------> Human Approval
                                  |
                                  v
                                 MCP
                                  |
                                  v
                            Ticket System

Agents

Supervisor Agent

The Supervisor is responsible for deciding which agent should handle the current request.

It uses the LLM for routing and does not perform the actual business operation itself.

Typical routes include:

* Knowledge Agent
* Ticket Agent
* Investigation Agent
* Action Agent
* General Agent

Knowledge Agent

The Knowledge Agent handles internal IT questions.

It uses the internal RAG system to retrieve relevant company documentation and uses the retrieved information to answer the user.

If the available documentation is not sufficient and the user has requested further investigation, the Knowledge Agent can hand off to the Investigation Agent.

The agent should not invent company-specific procedures or information that is not supported by the available documentation.

Investigation Agent

The Investigation Agent performs additional model-based analysis when the internal documentation is not sufficient.

It does not have an internet or web-search tool.

Therefore, it must clearly distinguish general model knowledge from information that has been verified against company documentation.

Ticket Agent

The Ticket Agent handles requests to view existing tickets.

Ticket operations are performed through MCP tools, and access is restricted according to the authenticated user’s identity and permissions.

Action Agent

The Action Agent handles actions that can change data, such as creating a support ticket.

It first prepares an action plan and creates a pending approval.

The workflow is then interrupted until a human approves or rejects the action.

If approved, the LangGraph workflow resumes from the stored checkpoint and the action is executed through MCP.

If rejected, the action is not executed.

General Agent

The General Agent handles greetings and general questions that do not require the service desk knowledge base or ticket system.

⸻

Agentic Handoff

One of the main agentic workflows is the following:

Supervisor
    |
    v
Knowledge Agent
    |
    +-- sufficient evidence --> Answer
    |
    +-- insufficient evidence
              |
              v
       Investigation Agent
              |
              +-- no action required --> Answer
              |
              +-- action required
                       |
                       v
                 Action Agent
                       |
                       v
                Human Approval
                   /        \
               Reject       Approve
                 |             |
                 v             v
                End           MCP
                                |
                                v
                          Ticket Operation

This allows the system to move between specialized agents based on the current request instead of sending every request through the same workflow.

The Investigation Agent is intentionally LLM-only. There is no Tavily, web-search API, or external search dependency in this workflow.

⸻

RAG

The knowledge workflow uses an internal document collection for IT support information.

The current knowledge base includes topics such as:

* VPN
* Company laptops
* Outlook
* Passwords
* Security

The retrieval process includes query rewriting and relevance checking before the Knowledge Agent generates its response.

The system is designed to avoid presenting unsupported information as company policy.

⸻

MCP

MCP is used as the tool integration layer between the agents and ticket-related operations.

The basic flow is:

Agent
  |
  v
MCP Client
  |
  | Streamable HTTP
  v
MCP Server
  |
  v
Ticket Tool
  |
  v
Database

This keeps the agent logic separate from the implementation of the underlying ticket operations.

Examples of MCP operations include:

create_ticket_for_user
search_my_tickets
get_ticket_for_user

Ticket creation also uses an idempotency key so that a retried operation does not unintentionally create duplicate tickets.

⸻

Memory

The application uses two types of memory.

Short-term memory

LangGraph checkpointing maintains the state of an active conversation and workflow.

The checkpoint is associated with the conversation thread_id.

This allows an interrupted workflow, such as a human approval request, to resume with the correct state.

Long-term memory

Long-term user-specific information is stored in the SQL Memory table.

Only explicit user preferences are intended to be stored, and the memory layer checks for sensitive information before saving it.

⸻

Human Approval

Actions that can modify data are not executed immediately.

For example:

User requests ticket
        |
        v
Action Agent
        |
        v
Prepare action
        |
        v
Create approval
        |
        v
LangGraph interrupt
        |
        +------ Reject ------> End
        |
        +------ Approve -----> Resume
                                  |
                                  v
                                 MCP

This provides a human-in-the-loop control point before a consequential operation is executed.

⸻

Security and Reliability

The API includes several supporting controls:

* Authentication and role-based authorization
* Request validation
* Prompt-injection guardrails
* Rate limiting
* User-scoped ticket access
* Idempotent ticket creation
* Structured application logging
* Audit logging
* Application metrics

These controls are separate from the agent reasoning layer and protect the overall application.

⸻

Deployment

For local development, the application can use SQLite for application data and local checkpointing.

The production deployment uses PostgreSQL for persistent application data.

The MCP server is deployed separately from the API and communicates with the API through Streamable HTTP.

The current RAG implementation uses the application’s retrieval store. For a larger production deployment, the retrieval layer can be moved to a managed or persistent vector/search store rather than relying on local filesystem storage.

⸻

Main Technology Stack

Area	Technology
API	FastAPI
Agent orchestration	LangGraph
LLM framework	LangChain
LLM	Groq / Ollama
RAG	Internal document retrieval
Tool integration	MCP
Database	PostgreSQL / SQLite
Cache	Redis
Authentication	JWT-based authentication
Deployment	Docker / Render
Observability	Structured logs, metrics and audit logs

The overall design separates the AI reasoning layer from the application, database, security, and tool-integration layers. This makes the system easier to extend with additional agents, tools, knowledge sources, and enterprise integrations.
# AWS IT Service Desk Agent

An AI-powered IT Service Desk Agent built with Python, FastAPI, LangGraph, and Amazon Bedrock, deployed on AWS using Amazon ECS Fargate.

The application demonstrates agentic AI workflows for IT support, service desk ticket management, MCP-based tool execution, human-in-the-loop approval, and persistent storage using Amazon RDS for PostgreSQL.

The architecture separates the main AI application from the MCP server and uses AWS Cloud Map for internal service discovery.

## Overview

The application provides an AI-driven interface for IT service desk operations.

Key capabilities include:

- AI-powered IT support conversations.
- LangGraph-based agent orchestration.
- Amazon Bedrock integration for LLM inference.
- Service desk ticket creation, searching, and retrieval.
- MCP-based integration between agents and backend tools.
- Human approval for consequential actions.
- PostgreSQL persistence using Amazon RDS.
- AWS Cloud Map for internal service discovery.
- Application logging and monitoring through Amazon CloudWatch.
- Containerized deployment using Amazon ECS Fargate.

The exact operations available depend on the tools implemented in the application.

---

## AWS Architecture

The application is deployed in the AWS Europe (Stockholm) Region (`eu-north-1`).

```text
                         User
                           |
                           v
                  Web Browser / Frontend
                           |
                           v
                Application Load Balancer
                      HTTP : 80
                           |
                           v
              +-------------------------+
              | Amazon ECS Fargate      |
              | Service: service-desk   |
              |                         |
              | FastAPI Application     |
              |                         |
              | LangGraph Agents        |
              |  - Supervisor           |
              |  - Knowledge Agent      |
              |  - Investigation Agent  |
              |  - Ticket Agent         |
              |  - Action Agent         |
              |  - General Agent        |
              |                         |
              | MCP Client              |
              +------------+------------+
                           |
                           | Internal HTTP
                           | Service Discovery
                           v
                 +----------------------+
                 | AWS Cloud Map        |
                 |                      |
                 | mcp.service-desk.local
                 +-----------+----------+
                             |
                             v
                +--------------------------+
                | Amazon ECS Fargate       |
                | Service: service-desk-mcp|
                |                          |
                | MCP Server               |
                | Ticket Tools             |
                | Backend Tools            |
                +------------+-------------+
                             |
                             v
                  +----------------------+
                  | Amazon RDS           |
                  | PostgreSQL           |
                  |                      |
                  | Database: servicedesk|
                  +----------------------+

       +--------------------+  +----------------------+
       | Amazon Bedrock      |  | Amazon ECR           |
       |                    |  |                      |
       | LLM Inference      |  | Container Images     |
       +--------------------+  +----------------------+

                  +----------------------+
                  | Amazon CloudWatch     |
                  | Application and ECS  |
                  | Logs                 |
                  +----------------------+
```

This is a logical architecture diagram. The exact network paths, subnet placement, and security-group rules are defined by the deployed AWS configuration.

### Main AWS Components

| AWS Service | Purpose |
|---|---|
| Amazon ECS Fargate | Runs the main FastAPI application and the separate MCP service. |
| Application Load Balancer | Provides the application entry point over HTTP on port 80. |
| Amazon Bedrock | Provides LLM inference for the AI agents. |
| AWS Cloud Map | Enables internal discovery of the MCP service. |
| Amazon RDS for PostgreSQL | Stores persistent application and service desk data. |
| Amazon ECR | Stores the container images used by ECS. |
| Amazon CloudWatch | Collects application and ECS logs. |
| AWS IAM | Controls permissions for AWS resource access. |
| AWS Secrets Manager | Supplies configured database credentials and secrets. |

No Amazon EFS or other unverified storage services are assumed in this architecture.

---

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Integration | LangChain |
| LLM Runtime | Amazon Bedrock |
| Model | Configured Bedrock inference profile |
| Tool Integration | Model Context Protocol (MCP) |
| Database | PostgreSQL |
| Database Hosting | Amazon RDS |
| Container Runtime | Amazon ECS Fargate |
| Container Registry | Amazon ECR |
| Service Discovery | AWS Cloud Map |
| Logging | Amazon CloudWatch |
| Secrets | AWS Secrets Manager |
| Access Control | AWS IAM |
| Load Balancing | Application Load Balancer |

The exact model and application configuration are controlled by the deployed task definitions and environment settings.

---

## Agentic AI Workflow

The application uses LangGraph to coordinate specialized agents and their handoffs.

```text
                       User Request
                            |
                            v
                       Supervisor
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
       Knowledge Agent  Ticket Agent  General Agent
             |
             v
      Internal RAG / Knowledge
             |
             v
     Insufficient Evidence?
             |
             v
    Investigation Agent
       (LLM-based)
             |
             v
        Action Agent
             |
             v
      Human Approval
             |
             v
        MCP Client
             |
             v
        MCP Server
             |
             v
      Backend Tool Execution
             |
             v
       PostgreSQL / Result
```

The actual workflow depends on the user's request and the graph's routing logic.

The Investigation Agent uses the configured LLM and does not perform internet searches. It must not claim external verification.

---

## Human-in-the-Loop Approval

Consequential operations can require human approval before execution.

The workflow separates the approval decision from the actual backend operation.

```text
Action Requested
       |
       v
Approval Created
       |
       v
Await Human Decision
       |
       +------ Rejected ------> Stop Action
       |
       +------ Approved
                  |
                  v
             MCP Execution
                  |
                  v
             Result Stored
```

The application checks the approval state before executing the relevant action.

Idempotency controls are used in the ticket-creation workflow to help prevent duplicate operations during retries.

The precise approval requirements depend on the operation and its implementation.

---

## MCP Integration and AWS Cloud Map

The main application and MCP server run as separate ECS services.

### Main Application

The `service-desk` ECS service hosts the FastAPI application and LangGraph agents.

The application uses an MCP client when a request requires supported backend tools.

### MCP Server

The `service-desk-mcp` ECS service hosts the MCP server and exposes the configured service desk tools.

Supported operations include ticket-related and other backend operations implemented by the MCP server.

### Service Discovery

AWS Cloud Map provides internal service discovery so that the main application can locate the MCP service without hardcoding a task's IP address.

The configured MCP endpoint is:

```text
http://mcp.service-desk.local:8001/mcp
```

This is an internal service-to-service HTTP endpoint, not the public application URL.

The endpoint must be resolvable from the main ECS task's network environment.

---

## Amazon Bedrock

Amazon Bedrock provides model inference for the AI agents.

The deployed application uses the configured Bedrock inference profile:

```text
eu.anthropic.claude-sonnet-4-6
```

The model is invoked through the AWS SDK and the permissions assigned to the application's ECS task role.

Model availability, invocation permissions, quotas, and costs depend on the AWS account and Region configuration.

---

## Database

The application uses Amazon RDS for PostgreSQL.

Configured database details:

| Setting | Value |
|---|---|
| Database engine | PostgreSQL |
| Database name | `servicedesk` |
| AWS Region | `eu-north-1` |
| Database access | Application services using configured credentials and network permissions |

The database stores service desk and application data used by the implemented workflows.

Database credentials should be supplied through the configured secrets-management mechanism rather than committed to source control.

Database access should remain restricted to authorized application services.

---

## Security

Security is enforced through a combination of application controls and AWS infrastructure permissions.

### AWS Security

- IAM roles control access to AWS services.
- ECS task roles provide application-level AWS permissions.
- AWS Secrets Manager stores configured sensitive values.
- Security groups restrict network access.
- RDS should not be exposed directly to the public internet.
- Internal service communication uses the configured private service-discovery endpoint.

### Application Security

- Input validation and sanitization.
- Approval checks for consequential actions.
- Backend validation before executing supported operations.
- Controlled tool execution through the MCP integration.
- Error handling and logging for application operations.

Application-level authentication and authorization features should be documented according to the controls actually enabled in the deployed application.

---

## Logging and Monitoring

Amazon CloudWatch collects logs from the ECS services.

Relevant log groups include:

```text
/ecs/service-desk
/ecs/service-desk-mcp
```

These logs can be used to investigate:

- Application errors.
- Agent execution.
- MCP requests.
- Ticket operations.
- Database connectivity.
- ECS task startup and runtime issues.

CloudWatch log retention, metrics, and alarms depend on the deployed AWS configuration.

---

## Container Images

The application and MCP server use separate container images stored in Amazon ECR.

```text
Amazon ECR
    |
    +-- service-desk image
    |
    +-- service-desk-mcp image
```

ECS retrieves the configured images when deploying or replacing tasks.

Image tags should be managed deliberately so that deployed versions can be identified and reproduced.

---

## Repository Structure

The project contains the application code, deployment-related files, frontend, and documentation.

```text
.
├── app/
│   ├── agents/           # LangGraph agents and orchestration
│   ├── database/         # Database configuration
│   ├── llm/              # LLM provider integration
│   ├── rag/              # Knowledge retrieval
│   ├── tools/            # Application tools
│   └── mcp/              # MCP client and server
├── frontend/             # Web interface
├── docs/                 # Architecture and deployment documentation
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── README.md
```

This is a representative structure. Refer to the actual repository for the complete list of files and directories.

---

## Deployment

The application runs on Amazon ECS Fargate.

The deployment consists of two ECS services:

| ECS Service | Responsibility |
|---|---|
| `service-desk` | FastAPI application and AI agents |
| `service-desk-mcp` | MCP server and backend tools |

The main application communicates with the MCP server through AWS Cloud Map.

Amazon RDS provides persistent database storage, Amazon Bedrock provides LLM inference, and Amazon CloudWatch collects logs.

The Application Load Balancer exposes the web application over HTTP on port 80.

For production use, HTTPS should be configured with an appropriate certificate and listener before exposing sensitive application traffic.

---

## Local Development

Local development requirements may differ from the deployed AWS configuration.

### Prerequisites

- Python compatible with the project dependencies.
- Git.
- Docker, if building or running containers locally.
- Appropriate environment variables.
- Access to any required database, LLM, and MCP services.

### Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Provide the environment variables required by the application, including the appropriate database and model-provider configuration.

Do not commit `.env` files, credentials, database dumps, or other sensitive configuration.

### Run the Application

```bash
uvicorn app.main:app --reload
```

The exact startup command and local service requirements should be verified against the current source code.

---

## Current Scope

This project demonstrates:

- Agent orchestration with LangGraph.
- LLM inference through Amazon Bedrock.
- Service desk tools exposed through MCP.
- Human approval for consequential actions.
- Internal service discovery through AWS Cloud Map.
- Persistent PostgreSQL storage.
- Containerized deployment using ECS Fargate.
- Application logging through CloudWatch.

The project is a proof of concept. Production readiness requires further validation of security, availability, resilience, operational monitoring, and deployment procedures.

---

## Future Improvements

Potential areas for further development include:

- HTTPS for the public application endpoint.
- Enterprise SSO and OAuth2 integration, where required.
- Integration with ServiceNow or Jira.
- Improved RAG evaluation.
- Distributed tracing.
- Expanded security and failure-recovery testing.
- Automated model and prompt evaluation.
- Improved deployment automation and infrastructure as code.

---

## Project Goal

The goal of this project is to demonstrate how agentic AI can support IT service desk workflows using AWS-managed infrastructure.

By combining LangGraph, Amazon Bedrock, MCP, AWS Cloud Map, Amazon ECS, and Amazon RDS, the project illustrates a modular architecture in which AI reasoning, backend tool execution, approval controls, and persistent storage are separated into independently managed components.
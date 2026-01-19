# Model Context Protocol (MCP) Notes

## Overview

The Model Context Protocol (MCP) allows the creation of servers that expose data and functionality to LLM applications in a secure and standardized manner. It is often referred to as the "USB-C port for AI," providing a uniform way to connect LLMs to resources. MCP servers can:

- Expose data through **Resources** (similar to GET endpoints)
- Provide functionality through **Tools** (similar to POST endpoints)
- Define interaction patterns through **Prompts** (reusable templates for LLM interactions)

## Core MCP Primitives

MCP defines three main components that establish a standard for interactions between LLMs and external systems:

Resources: Your AI’s Information Library
Resources are standardized gateways to data sources. Resources provide a consistent interface, whether you’re accessing customer information from a CRM system, financial data from a database, or documents from a file system.

Think of resources as librarians who know precisely where to find any book you need, regardless of how they structure the library internally. A resource might look like:

customer://crm-server/customer/12345
file://documents/contracts/latest.pdf
database://analytics/sales-report?quarter=Q3
Tools: Your AI’s Hands and Feet
While resources provide information, tools enable action. Tools are functions that your AI can execute to perform tasks — from simple calculations to complex workflows.

Tools transform AI from passive information consumers into active problem-solvers that can:

Calculate mortgage payments
Send emails
Update database records
Generate reports
Analyze sentiment in text
Prompts: Your AI’s Instruction Manual
Prompts in MCP go beyond simple text instructions. They’re structured templates that guide AI behavior and extract specific information. A well-crafted prompt acts like a detailed recipe, ensuring consistent and accurate AI responses.

Sampling: Your AI’s Learning Mechanism
Sampling enables AI systems to request content generation and collect feedback for continuous improvement. This creates learning loops that help AI systems get better over time.

## How LLMs Enable Tool Use

Tool Discovery: The AI model receives descriptions of available tools and their parameters
Intent Recognition: Based on user input, the model determines which tools are needed
Parameter Extraction: The model extracts the necessary parameters from the conversation context
Tool Invocation: The model generates a structured request to call the appropriate tool
Result Integration: The tool’s output is incorporated back into the conversation flow

## FAST MCP 2.0

- **Transport Options**:
  - **STDIO**: Default for local tools.
  - **HTTP**: Recommended for web services, uses Streamable HTTP protocol.
  - **SSE**: Legacy web transport, deprecated.

## MCP Inspector

```
npx @modelcontextprotocol/inspector python fastmcp_calculator.py
```

\*\* Run STDIO by default

\*\* add below args for http

```
fastmcp run ./quickstart.py --transport http --port 8000
```

## FastMCP Server (overview)

FastMCP is a lightweight server framework for exposing Resources, Tools, and Prompts to LLM clients using the MCP standard. For a practical learning guide and examples (creating servers, constructor options, components, transports, and integrations) see: [fastmcp_server_guide.md](fastmcp_server_guide.md)

ref: https://medium.com/@richardhightower/mcp-from-chaos-to-harmony-building-ai-integrations-with-the-model-context-protocol-98123d374ac4

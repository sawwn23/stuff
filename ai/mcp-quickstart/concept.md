# Model Context Protocol (MCP) Notes

## Overview

The Model Context Protocol (MCP) allows the creation of servers that expose data and functionality to LLM applications in a secure and standardized manner. It is often referred to as the "USB-C port for AI," providing a uniform way to connect LLMs to resources. MCP servers can:

- Expose data through **Resources** (similar to GET endpoints)
- Provide functionality through **Tools** (similar to POST endpoints)
- Define interaction patterns through **Prompts** (reusable templates for LLM interactions)

## Core MCP Primitives

MCP defines three main components that establish a standard for interactions between LLMs and external systems:

### 1. Resources: The LLM's Eyes

- **Function**: Provide context by exposing data directly to the LLM.
- **Behavior**: Like GET endpoints in REST APIs, they retrieve data without modification.
- **Example**: `health://steps/latest` - retrieves the most recent step records.
- **URI Pattern**: Use domain-namespaced patterns.

### 2. Tools: The LLM's Hands

- **Function**: Enable action and computation, essential for complex queries and analyses.
- **Behavior**: Like POST endpoints in REST APIs, they execute operations and can have side effects.
- **Characteristics**:
  - Accept structured parameters.
  - Dynamic logic based on parameters.
  - Active processing and data manipulation, not just data retrieval.

### 3. Prompts: The Maps for the LLM

- **Function**: Provide reusable command templates for common tasks, differing from traditional LLM prompts.
- **Behavior**: Registered templates that appear as slash commands.
- **Example**: `/daily_report` - triggers a pre-configured analysis workflow.
- **Purpose**: Standardize common interactions and workflows.

## FAST MCP 2.0

- **Transport Options**:
  - **STDIO**: Default for local tools.
  - **HTTP**: Recommended for web services, uses Streamable HTTP protocol.
  - **SSE**: Legacy web transport, deprecated.

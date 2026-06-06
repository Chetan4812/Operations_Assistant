# Decision Log - Operations Assistant

This document log outlines the key architectural decisions made during the design and development of the Operations Assistant multi-agent system.

## 1. Multi-Server MCP Architecture vs Single-Server
- **Choice**: Separated into two distinct servers: `servers/data_server.py` (read-only tools & resources) and `servers/reporting_server.py` (write-only reports tool).
- **Rationale**: 
  - **Security**: Segregation of duties. The `Operations Researcher` and `Operations Analyst` only have access to retrieve data. The `Operations Reporter` and `Self-Check Auditor` handle saving data. By hosting them on separate processes, we enforce strict privilege boundaries at the OS process level.
  - **Scalability**: Subprocesses can be scaled, maintained, and updated independently.
- **Alternatives Rejected**: A single large server exposing all tools. This would expose write tools to all agents, increasing the risk of unauthorized write actions in case of agent hijacking (e.g. prompt injection).

## 2. Windows Ctypes MessageBox for Human Approval Gate
- **Choice**: Native Windows Graphical Dialog box via `ctypes.windll.user32.MessageBoxW`.
- **Rationale**: 
  - **Protocol Interference**: Since MCP runs over `stdio` in standard environments, any console `input()` prompt from a subprocess blocks the JSON-RPC pipe and corrupts the stream, leading to transport errors and client crashes.
  - **Interactive Pop-up**: Pop-ups run in a separate thread/window on Windows, blocking the specific file-writing thread until the user clicks **Yes** or **No**, without affecting standard stream channels.
- **Alternatives Rejected**:
  - Console `input()`: Blocked and corrupted stdio transport streams.
  - Automatic writes: Disqualified because human approval was a strict requirement.

## 3. Dedicated Self-Check Verification Agent
- **Choice**: Added a 4th agent (`Self-Check Auditor`) to verify final reports against raw context.
- **Rationale**:
  - Prevents hallucinations by checking whether each claim is fully grounded.
  - Acts as a security firewall, scanning the generated report for malicious formatting or instructions (e.g., prompt injections trying to write to `compromised.md` instead of the standard target folder).
- **Alternatives Rejected**: Standard writing task without check steps. Under testing, models directly writing reports sometimes omitted details or hallucinated statuses.

## 4. LLM Infrastructure - Groq vs Local Ollama
- **Choice**: Configured for `groq/llama-3.1-8b-instant` via LiteLLM.
- **Rationale**:
  - **Latency**: Groq's high-speed inference provides immediate responses, essential for multi-agent loops which can take multiple iterations.
  - **Reliability**: Excellent tool calling capability compared to smaller 8B models running locally on standard laptop hardware.
  - **Portability**: Configured via environmental variables (`GROQ_API_KEY`) so that a fresh clone only needs a `.env` file key.

# AI Usage Log

This log lists how AI-assisted engineering was used during the construction, debugging, and verification of the Operations Assistant project.

## 1. System Design & Brainstorming
- **Activity**: Formulating the security architecture for the prompt-injection and human approval gate.
- **AI Assist**: Brainstormed alternatives to prevent blocking stdio MCP transports when requesting human interaction. The AI suggested the ctypes-based GUI popup approach on Windows, which isolates standard output and input streams from standard process pipes.

## 2. MCP Server Implementation
- **Activity**: Implementing `servers/data_server.py` and `servers/reporting_server.py`.
- **AI Assist**: Synthesized standard FastMCP decorators, tool structures, Pydantic type annotation schemas (`Annotated[str, Field(pattern=...)]`), and safe path retrieval constraints.

## 3. CrewAI Core Setup
- **Activity**: Designing agents, context propagation, and custom traces.
- **AI Assist**: Assisted in designing the custom `step_callback` function, mapping LiteLLM parameters to the `LLM` constructor, and wiring up sequentially dependent tasks.

## 4. Test Creation
- **Activity**: Writing mock-heavy pytest code.
- **AI Assist**: Wrote `unittest.mock.patch` calls to mock `ctypes.windll.user32.MessageBoxW` to return custom code values (6 for Yes, 7 for No) to verify write tools in unit and E2E tests without halting in head-free environments.

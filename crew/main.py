import os
import sys

# Monkey-patch to disable unsupported cache_breakpoint in CrewAI for Groq API
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except ImportError:
    pass

from dotenv import load_dotenv
from crewai import Crew, LLM, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

# 1. Load Environment Variables
# If running directly, load .env file
load_dotenv()

# Verify GROQ_API_KEY is present
if not os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY") in ["your_groq_api_key_here", ""]:
    print("WARNING: GROQ_API_KEY is not set or is still a placeholder in .env.", file=sys.stderr)
    print("Please set GROQ_API_KEY in your environment or in the .env file.", file=sys.stderr)

# Add project root to sys.path to enable absolute imports in all execution contexts
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crew.agents import create_researcher, create_analyst, create_writer, create_verifier
from crew.tasks import (
    create_research_task,
    create_analysis_task,
    create_writing_task,
    create_verification_task
)

def run_operations_assistant(query: str):
    print(f"\n[System] Starting Operations Assistant Crew for query: '{query}'")

    # 2. Configure the LLM
    model_name = os.environ.get("MODEL_NAME", "groq/llama-3.1-8b-instant")
    print(f"[System] Initializing LLM: {model_name}")
    
    # Initialize CrewAI LLM (LiteLLM routes 'groq/*' automatically using GROQ_API_KEY)
    llm = LLM(
        model=model_name,
        temperature=0.0,
        api_key=os.environ.get("GROQ_API_KEY")
    )

    # 3. Setup MCP Stdio server parameters
    # Use the current python interpreter to run the subprocess server scripts
    python_path = sys.executable
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    print("[System] Configured MCP Data Server parameters")
    data_server_params = StdioServerParameters(
        command=python_path,
        args=[os.path.join(project_dir, "servers", "data_server.py")],
        env={**os.environ, "PYTHONPATH": project_dir}
    )

    print("[System] Configured MCP Reporting Server parameters")
    reporting_server_params = StdioServerParameters(
        command=python_path,
        args=[os.path.join(project_dir, "servers", "reporting_server.py")],
        env={**os.environ, "PYTHONPATH": project_dir}
    )

    # 4. Tracing Setup
    trace_path = os.environ.get("TRACE_FILE_PATH", os.path.join(project_dir, "output", "run_trace.txt"))
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    
    # Clean the old trace file if it exists
    with open(trace_path, "w", encoding="utf-8") as f:
        f.write(f"--- OPERATIONS ASSISTANT RUN TRACE ---\nQuery: {query}\n\n")

    def step_callback(step_output):
        """Callback to log every step of the agent execution to a file."""
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write("\n" + "="*40 + "\n")
            f.write(f"AGENT STEP DETAIL:\n")
            try:
                # Convert the StepOutput to a string representation safely
                f.write(str(step_output))
            except Exception as e:
                f.write(f"[Error printing step output]: {e}")
            f.write("\n" + "="*40 + "\n")

    # 5. Run within MCPServerAdapter context
    print("[System] Connecting to MCP Data Server and MCP Reporting Server...")
    try:
        with MCPServerAdapter(data_server_params) as data_tools, \
             MCPServerAdapter(reporting_server_params) as reporting_tools:
            
            print(f"[System] Connected! Found {len(data_tools)} tools from Data Server and {len(reporting_tools)} tools from Reporting Server.")
            
            # Map tools
            # data_tools exposes search_documents, read_record
            # reporting_tools exposes save_report

            # Initialize Agents
            researcher = create_researcher(llm, data_tools)
            analyst = create_analyst(llm, data_tools)
            writer = create_writer(llm, [])
            # Verifier needs reporting tools to save the file, and data tools to check facts
            verifier = create_verifier(llm, data_tools + reporting_tools)

            # Assign step callback to agents for step-by-step tracing
            researcher.step_callback = step_callback
            analyst.step_callback = step_callback
            writer.step_callback = step_callback
            verifier.step_callback = step_callback

            # Create Tasks
            # Research Task
            task_research = create_research_task(researcher)
            # Analysis Task
            task_analysis = create_analysis_task(analyst)
            # Writing Task combines context from Research and Analysis
            task_write = create_writing_task(writer, context=[task_research, task_analysis])
            # Verification Task reviews draft and saves it
            task_verify = create_verification_task(verifier, context=[task_write])

            # Setup Crew
            crew = Crew(
                agents=[researcher, analyst, writer, verifier],
                tasks=[task_research, task_analysis, task_write, task_verify],
                process=Process.sequential,
                verbose=True
            )

            # Kickoff Crew
            print("[System] Running the operations assistant crew. Please monitor the agents' steps...\n")
            result = crew.kickoff(inputs={"query": query})
            
            print("\n" + "#"*40)
            print("FINAL CREW OUTPUT:")
            print("#"*40)
            print(result)
            print("#"*40 + "\n")
            
            print(f"[System] Crew run completed. Step traces have been saved to: {trace_path}")
            return result

    except Exception as e:
        print(f"\n[System Error] Execution failed: {e}", file=sys.stderr)
        raise e

if __name__ == "__main__":
    print("="*50)
    print("  Operations Assistant Multi-Agent Crew Runner")
    print("="*50)
    
    # Check if a query was passed as command line arguments
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your query: ").strip()
        if not query:
            query = "Check the return policy details, verify the status of order 5002, and write a summary report."
            print(f"No query entered. Using default query: '{query}'")
            
    run_operations_assistant(query)

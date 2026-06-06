import ctypes
import os
import re
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated

# Create a FastMCP instance
mcp = FastMCP("Operations Reporting Server")

REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "reports"))

@mcp.tool()
def save_report(
    title: Annotated[str, Field(min_length=3, max_length=50, description="The alphanumeric title of the report.")],
    content: Annotated[str, Field(min_length=10, description="The markdown content of the report.")]
) -> str:
    """Save a report to the output folder. Requires human approval."""
    # 1. Input Validation
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", title):
        return "Error: Title contains invalid characters. Only alphanumeric, spaces, hyphens, and underscores are allowed."
    
    # 2. Path Traversal Guardrail
    filename = f"{title.replace(' ', '_').lower()}.md"
    target_path = os.path.abspath(os.path.join(REPORT_DIR, filename))
    if not target_path.startswith(os.path.abspath(REPORT_DIR)):
        return "Error: Path traversal detected. Writing outside the reports directory is forbidden."
    
    # 3. Human Approval Gate
    try:
        # MB_YESNO = 4, MB_ICONQUESTION = 0x20
        # Returns 6 for Yes, 7 for No
        box_text = (
            f"An agent wants to save the following report:\n\n"
            f"Title: {title}\n\n"
            f"Content Snippet:\n"
            f"{content[:300]}...\n\n"
            f"Do you approve saving this report to disk?"
        )
        response = ctypes.windll.user32.MessageBoxW(0, box_text, "Operations Assistant - Action Approval", 4 | 0x20)
        if response != 6:
            return "Error: Action rejected by the user. Report was not saved."
    except Exception as e:
        # Fallback log to stderr in case UI is not interactive
        import sys
        print(f"MessageBox error: {e}", file=sys.stderr, flush=True)
        return "Error: Failed to obtain human approval via graphical pop-up."

    # 4. Write File
    try:
        os.makedirs(REPORT_DIR, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Report saved to {target_path}."
    except Exception as e:
        return f"Error saving report: {str(e)}"

if __name__ == "__main__":
    mcp.run()

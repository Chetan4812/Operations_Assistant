from mcp.server.fastmcp import FastMCP
import os
import csv
import re
from pydantic import Field
from typing import Annotated

# Create a FastMCP instance
mcp = FastMCP("Operations Data Server")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DOCS_DIR = os.path.join(DATA_DIR, "documents")
ORDERS_CSV = os.path.join(DATA_DIR, "orders.csv")

@mcp.tool()
def search_documents(
    query: Annotated[str, Field(min_length=3, max_length=100, description="The search query to match against document contents. Must be alphanumeric and 3-100 characters.")]
) -> str:
    """Search operations guidelines, shipping notes, policies, and tickets for a query."""
    # Strict validation
    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", query):
        return "Error: Query contains invalid characters. Only alphanumeric, spaces, hyphens, and underscores are allowed."

    if not os.path.isdir(DOCS_DIR):
        return "Error: Documents directory not found."

    results = []
    # Search documents safely
    for filename in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, filename)
        # Prevent reading outside directory
        if not os.path.realpath(file_path).startswith(os.path.realpath(DOCS_DIR)):
            continue
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        results.append(f"--- Document: {filename} ---\n{content}\n")
            except Exception as e:
                results.append(f"Error reading {filename}: {str(e)}")

    if not results:
        return f"No documents matched query: '{query}'."
    return "\n".join(results)

@mcp.tool()
def read_record(
    id: Annotated[str, Field(pattern=r"^\d{4}$", description="The 4-digit numeric order ID to retrieve (e.g. 5001).")]
) -> str:
    """Read a specific customer order record from the orders spreadsheet by order ID."""
    if not os.path.isfile(ORDERS_CSV):
        return "Error: Orders CSV file not found."

    try:
        with open(ORDERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("order_id") == id:
                    return (
                        f"Order ID: {row['order_id']}\n"
                        f"Customer Name: {row['customer_name']}\n"
                        f"Product: {row['product']}\n"
                        f"Quantity: {row['quantity']}\n"
                        f"Status: {row['status']}\n"
                        f"Order Date: {row['order_date']}\n"
                        f"Total Amount: ${row['total_amount']}"
                    )
        return f"Error: Order ID {id} not found in the orders spreadsheet."
    except Exception as e:
        return f"Error reading orders CSV: {str(e)}"

@mcp.resource("documents://list")
def list_documents() -> str:
    """List all available documents in the knowledge directory."""
    if not os.path.isdir(DOCS_DIR):
        return "Error: Documents directory not found."
    
    docs = []
    for filename in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, filename)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            docs.append(f"- {filename} ({size} bytes)")
    return "Available Documents:\n" + "\n".join(docs)

if __name__ == "__main__":
    mcp.run()

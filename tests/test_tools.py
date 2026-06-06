import sys
import os
import pytest
from unittest.mock import patch

# Add parent directory to sys.path to enable direct server imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from servers.data_server import search_documents, read_record
from servers.reporting_server import save_report

def test_search_documents():
    # Test a valid query matching document contents
    res = search_documents("Return Policy")
    assert "Return Policy" in res or "Returns" in res
    
    # Test invalid characters that violate input validation
    res_invalid_chars = search_documents("Return; rm -rf")
    assert "Error:" in res_invalid_chars
    
    # Test query that yields no matches
    res_empty = search_documents("nonexistentpattern123")
    assert "No documents matched" in res_empty

def test_read_record():
    # Test a valid existing order ID from orders.csv
    res = read_record("5001")
    assert "John Doe" in res
    assert "Widget A" in res
    
    # Test a non-existent order ID
    res_none = read_record("9999")
    assert "Error:" in res_none or "not found" in res_none

@patch("ctypes.windll.user32.MessageBoxW")
def test_save_report_success(mock_messagebox):
    # Mock user approval to click "Yes" (returns 6)
    mock_messagebox.return_value = 6
    
    title = "unit_test_report"
    content = "This is a mock report content for checking tool save logic."
    
    res = save_report(title, content)
    assert "Success:" in res
    
    # Verify file exists and clean it up
    report_file = os.path.join(os.path.dirname(__file__), "..", "output", "reports", "unit_test_report.md")
    assert os.path.exists(report_file)
    
    # Cleanup
    if os.path.exists(report_file):
        os.remove(report_file)

@patch("ctypes.windll.user32.MessageBoxW")
def test_save_report_rejection(mock_messagebox):
    # Mock user rejection to click "No" (returns 7)
    mock_messagebox.return_value = 7
    
    res = save_report("rejected_report", "Content should not write to disk.")
    assert "Error: Action rejected" in res
    
    report_file = os.path.join(os.path.dirname(__file__), "..", "output", "reports", "rejected_report.md")
    assert not os.path.exists(report_file)

def test_save_report_traversal():
    # Check invalid characters (like '/') preventing traversal
    res = save_report("subdir/report", "Should fail validation.")
    assert "Error: Title contains invalid characters" in res

import sys
import os
import pytest
from unittest.mock import patch

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crew.main import run_operations_assistant

@patch("ctypes.windll.user32.MessageBoxW")
def test_e2e_crew(mock_messagebox):
    # Mock user approval (returns 6 for IDYES)
    mock_messagebox.return_value = 6
    
    query = "Check return policy guidelines, verify the details of order 5002, and save a summary report."
    
    try:
        # Run the crew
        result = run_operations_assistant(query)
        assert result is not None
        
        # Verify that a report was saved in the output/reports directory
        report_dir = os.path.join(os.path.dirname(__file__), "..", "output", "reports")
        assert os.path.exists(report_dir), "Reports output directory does not exist."
        
        files = os.listdir(report_dir)
        assert len(files) > 0, "No report files were saved by the crew."
        
        # Clean up files saved during E2E test
        for f in files:
            os.remove(os.path.join(report_dir, f))
            
    except Exception as e:
        pytest.fail(f"E2E crew test failed: {e}")

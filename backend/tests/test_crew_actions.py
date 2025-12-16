
import pytest
from unittest.mock import MagicMock
from backend.utils.crew_actions import handle_table_format

def test_handle_table_format():
    # Mock section_config
    section_config = {
        "section_name": "Budget",
        "instructions": "Test instructions",
        "columns": [
            {"name": "Budget Line Description"},
            {"name": "Total cost (USD)"}
        ],
        "rows": []
    }

    # Mock crew_instance
    mock_crew_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.raw = '''
    {
        "generated_content": {
            "Budget": {
                "table": [
                    {
                        "Budget Line Description": "Project management and field staff",
                        "Total cost (USD)": 900000
                    },
                    {
                        "Budget Line Description": "Educational supplies",
                        "Total cost (USD)": 300000
                    }
                ],
                "notes": "Test notes"
            }
        },
        "evaluation_status": "Approved",
        "feedback": ""
    }
    '''
    mock_crew_instance.kickoff.return_value = mock_result

    # Call the function
    markdown_table = handle_table_format(section_config, mock_crew_instance, {}, "")

    # Assertions
    expected_table = """| Budget Line Description | Total cost (USD) |
| --- | --- |
| Project management and field staff | 900000 |
| Educational supplies | 300000 |
Test notes"""
    assert expected_table in markdown_table

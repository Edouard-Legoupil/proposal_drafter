import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import json
from datetime import datetime

from backend.core.config import load_proposal_template


@pytest.fixture
def mock_template_service():
    """Mock template service for testing"""
    mock_service = MagicMock()
    return mock_service


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    mock_conn = MagicMock()
    mock_conn.execute.return_value = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_conn.execute.return_value = mock_result
    return mock_conn


def test_load_proposal_template_file_fallback():
    """Test that template loading falls back to file system when DB fails"""
    
    # Mock the database to return None
    with patch('backend.core.config._load_template_from_db') as mock_db_load, \
         patch('backend.core.config.get_available_templates') as mock_get_templates, \
         patch('backend.core.config._find_template_path') as mock_find_path, \
         patch('builtins.open', create=True) as mock_open, \
         patch('json.load') as mock_json_load:
        
        # Setup mocks
        mock_db_load.return_value = None
        mock_get_templates.return_value = {"test.json": "test.json"}
        mock_find_path.return_value = "/path/to/test.json"
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_json_load.return_value = {"template_name": "Test Template"}
        
        # Call the function
        result = load_proposal_template("test.json")
        
        # Verify behavior
        mock_db_load.assert_called_once_with("test.json")
        mock_find_path.assert_called_once_with("test.json")
        mock_open.assert_called_once_with("/path/to/test.json", "r", encoding="utf-8")
        assert result == {"template_name": "Test Template"}


def test_load_proposal_template_db_success():
    """Test that template loading uses DB when available"""
    
    # Mock the database to return template data
    with patch('backend.core.config._load_template_from_db') as mock_db_load:
        mock_db_load.return_value = {"template_name": "DB Template", "db_source": True}
        
        # Call the function
        result = load_proposal_template("test.json")
        
        # Verify behavior
        mock_db_load.assert_called_once_with("test.json")
        assert result == {"template_name": "DB Template", "db_source": True}


def test_load_proposal_template_not_found():
    """Test error handling when template not found"""
    
    with patch('backend.core.config._load_template_from_db') as mock_db_load, \
         patch('backend.core.config.get_available_templates') as mock_get_templates:
        
        # Setup mocks to simulate not found
        mock_db_load.return_value = None
        mock_get_templates.return_value = {}
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            load_proposal_template("nonexistent.json")
        
        assert "not found" in str(exc_info.value).lower()


def test_load_proposal_template_file_error():
    """Test error handling when file parsing fails"""
    
    with patch('backend.core.config._load_template_from_db') as mock_db_load, \
         patch('backend.core.config.get_available_templates') as mock_get_templates, \
         patch('backend.core.config._find_template_path') as mock_find_path, \
         patch('builtins.open', create=True) as mock_open:
        
        # Setup mocks to simulate file error
        mock_db_load.return_value = None
        mock_get_templates.return_value = {"test.json": "test.json"}
        mock_find_path.return_value = "/path/to/test.json"
        
        # Simulate JSON decode error
        mock_open.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            load_proposal_template("test.json")
        
        assert "parsing" in str(exc_info.value).lower()


def test_load_proposal_template_db_fallback_disabled():
    """Test that use_db_first=False skips database loading"""
    
    with patch('backend.core.config._load_template_from_db') as mock_db_load, \
         patch('backend.core.config.get_available_templates') as mock_get_templates, \
         patch('backend.core.config._find_template_path') as mock_find_path, \
         patch('builtins.open', create=True) as mock_open, \
         patch('json.load') as mock_json_load:
        
        # Setup mocks
        mock_get_templates.return_value = {"test.json": "test.json"}
        mock_find_path.return_value = "/path/to/test.json"
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_json_load.return_value = {"template_name": "File Template"}
        
        # Call with use_db_first=False
        result = load_proposal_template("test.json", use_db_first=False)
        
        # Verify database was not called
        mock_db_load.assert_not_called()
        assert result == {"template_name": "File Template"}


@pytest.mark.asyncio
async def test_template_service_integration():
    """Test the complete template service workflow"""
    
    from backend.services.template_service import TemplateService
    from backend.models.template_models import TemplateCreate
    
    # Create mock database pool
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    service = TemplateService(mock_pool)
    
    # Test data
    template_data = {
        "template_name": "Integration Test Template",
        "sections": [{"section_name": "Test Section"}]
    }
    
    create_request = TemplateCreate(
        name="Integration Test",
        filename="integration_test.json",
        template_type="proposal",
        description="Test template",
        template_data=template_data,
        version_notes="Initial version"
    )
    
    # Mock database responses
    template_id = uuid.uuid4()
    version_id = uuid.uuid4()
    
    mock_template_row = {
        "id": template_id,
        "name": "Integration Test",
        "filename": "integration_test.json",
        "template_type": "proposal",
        "description": "Test template",
        "status": "draft",
        "is_default": False,
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    mock_version_row = {
        "id": version_id,
        "template_id": template_id,
        "version_number": "1.0",
        "version_notes": "Initial version",
        "status": "active",
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    mock_conn.fetchrow.side_effect = [mock_template_row, mock_version_row]
    mock_conn.execute.return_value = None
    
    # Test template creation
    user_id = uuid.uuid4()
    result = await service.create_template(create_request, user_id)
    
    assert result is not None
    assert result["template"]["name"] == "Integration Test"
    assert result["version"]["version_number"] == "1.0"
    
    # Test template retrieval
    mock_conn.fetchrow.return_value = {
        **mock_template_row,
        "version_number": "1.0",
        "template_data": json.dumps(template_data),
        "version_status": "active"
    }
    
    retrieved = await service.get_template_by_filename("integration_test.json")
    assert retrieved is not None
    assert retrieved["name"] == "Integration Test"


@pytest.mark.asyncio
async def test_template_versioning():
    """Test template version creation and management"""
    
    from backend.services.template_service import TemplateService
    from backend.models.template_models import TemplateVersionCreate
    
    # Create mock database pool
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    service = TemplateService(mock_pool)
    
    template_id = uuid.uuid4()
    
    # Test initial version creation
    version_data = TemplateVersionCreate(
        version_notes="Updated with new sections",
        template_data={"updated": "template"}
    )
    
    mock_version_row = {
        "id": uuid.uuid4(),
        "template_id": template_id,
        "version_number": "1.1",
        "version_notes": "Updated with new sections",
        "status": "active",
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    mock_conn.fetchrow.return_value = mock_version_row
    mock_conn.execute.return_value = None
    
    user_id = uuid.uuid4()
    result = await service.create_template_version(template_id, version_data, user_id)
    
    assert result is not None
    assert result["version_number"] == "1.1"
    assert result["version_notes"] == "Updated with new sections"


@pytest.mark.asyncio
async def test_template_donor_mapping():
    """Test donor-template mapping functionality"""
    
    from backend.services.template_service import TemplateService
    
    # Create mock database pool
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    service = TemplateService(mock_pool)
    
    template_id = uuid.uuid4()
    
    # Mock donor data
    mock_donor_rows = [
        {
            "id": uuid.uuid4(),
            "name": "Test Donor 1",
            "account_id": "DONOR001",
            "donor_group": "Private Foundation"
        },
        {
            "id": uuid.uuid4(),
            "name": "Test Donor 2",
            "account_id": "DONOR002",
            "donor_group": "Government"
        }
    ]
    
    mock_conn.fetch.return_value = mock_donor_rows
    
    result = await service.get_template_donors(template_id)
    
    assert result is not None
    assert len(result) == 2
    assert result[0]["name"] == "Test Donor 1"
    assert result[1]["name"] == "Test Donor 2"


@pytest.mark.asyncio
async def test_template_audit_logging():
    """Test that template actions are properly logged"""
    
    from backend.services.template_service import TemplateService
    from backend.models.template_models import TemplateUpdate
    
    # Create mock database pool
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    service = TemplateService(mock_pool)
    
    template_id = uuid.uuid4()
    
    # Mock update response
    mock_updated_row = {
        "id": template_id,
        "name": "Updated Template",
        "filename": "test.json",
        "template_type": "proposal",
        "description": "Updated description",
        "status": "active",
        "is_default": False,
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    mock_conn.fetchrow.return_value = mock_updated_row
    mock_conn.execute.return_value = None
    
    update_data = TemplateUpdate(
        name="Updated Template",
        description="Updated description",
        status="active"
    )
    
    user_id = uuid.uuid4()
    result = await service.update_template_metadata(template_id, update_data, user_id)
    
    # Verify that execute was called for both update and audit log
    assert mock_conn.execute.call_count >= 2  # Update + audit log
    
    # Check that audit log was called with correct parameters
    audit_log_calls = [call for call in mock_conn.execute.call_args_list 
                      if 'template_audit_log' in str(call)]
    assert len(audit_log_calls) > 0


def test_backward_compatibility():
    """Test that existing template loading code still works"""
    
    # This tests the actual import paths used by existing code
    from backend.api.proposals import load_proposal_template
    from backend.api.knowledge import load_proposal_template as knowledge_load_template
    from backend.api.documents import load_proposal_template as documents_load_template
    
    # All should point to the same function
    assert load_proposal_template is knowledge_load_template
    assert load_proposal_template is documents_load_template
    
    # Verify the function signature is unchanged
    import inspect
    sig = inspect.signature(load_proposal_template)
    params = list(sig.parameters.keys())
    
    assert 'template_name' in params
    assert 'use_db_first' in params  # New parameter should be optional
    assert sig.parameters['use_db_first'].default is True
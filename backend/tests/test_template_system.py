import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import json
from datetime import datetime

from backend.services.template_service import TemplateService
from backend.models.template_models import TemplateCreate, TemplateUpdate, TemplateVersionCreate


@pytest.fixture
def mock_db_pool():
    """Create a mock database pool"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    return mock_pool


@pytest.fixture
def template_service(mock_db_pool):
    """Create template service with mock database"""
    return TemplateService(mock_db_pool)


@pytest.fixture
def sample_template_data():
    """Sample template data for testing"""
    return {
        "template_name": "Test Proposal Template",
        "template_type": "proposal",
        "description": "A test proposal template",
        "donors": ["Test Donor"],
        "sections": [
            {
                "section_name": "Executive Summary",
                "instructions": "Write a brief executive summary",
                "word_limit": 250
            }
        ]
    }


@pytest.fixture
def sample_template_create(sample_template_data):
    """Sample template creation request"""
    return TemplateCreate(
        name="Test Proposal Template",
        filename="test_proposal_template.json",
        template_type="proposal",
        description="A test proposal template",
        template_data=sample_template_data,
        version_notes="Initial version",
        donor_ids=[uuid.uuid4()]
    )


@pytest.mark.asyncio
async def test_get_template_by_filename_not_found(template_service):
    """Test getting template by filename when not found"""
    # Mock the database query to return None
    template_service.db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = None
    
    result = await template_service.get_template_by_filename("nonexistent.json")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_template_by_filename_found(template_service):
    """Test getting template by filename when found"""
    mock_row = {
        "id": uuid.uuid4(),
        "name": "Test Template",
        "filename": "test.json",
        "template_type": "proposal",
        "description": "Test description",
        "status": "active",
        "is_default": False,
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow(),
        "version_number": "1.0",
        "template_data": json.dumps({"test": "data"}),
        "version_status": "active"
    }
    
    template_service.db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
    
    result = await template_service.get_template_by_filename("test.json")
    
    assert result is not None
    assert result["name"] == "Test Template"
    assert result["filename"] == "test.json"


@pytest.mark.asyncio
async def test_create_template_success(template_service, sample_template_create):
    """Test successful template creation"""
    mock_template_row = {
        "id": uuid.uuid4(),
        "name": sample_template_create.name,
        "filename": sample_template_create.filename,
        "template_type": sample_template_create.template_type,
        "description": sample_template_create.description,
        "status": "draft",
        "is_default": False,
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    mock_version_row = {
        "id": uuid.uuid4(),
        "template_id": mock_template_row["id"],
        "version_number": "1.0",
        "version_notes": sample_template_create.version_notes,
        "status": "active",
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    # Mock the database operations
    mock_conn = template_service.db_pool.acquire.return_value.__aenter__.return_value
    mock_conn.fetchrow.side_effect = [mock_template_row, mock_version_row]
    mock_conn.execute.return_value = None  # For donor mapping
    
    user_id = uuid.uuid4()
    result = await template_service.create_template(sample_template_create, user_id)
    
    assert result is not None
    assert "template" in result
    assert "version" in result
    assert result["template"]["name"] == sample_template_create.name
    assert result["version"]["version_number"] == "1.0"


@pytest.mark.asyncio
async def test_update_template_metadata(template_service):
    """Test updating template metadata"""
    template_id = uuid.uuid4()
    update_data = TemplateUpdate(
        name="Updated Template Name",
        description="Updated description",
        status="active"
    )
    
    mock_updated_row = {
        "id": template_id,
        "name": "Updated Template Name",
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
    
    mock_conn = template_service.db_pool.acquire.return_value.__aenter__.return_value
    mock_conn.fetchrow.return_value = mock_updated_row
    
    user_id = uuid.uuid4()
    result = await template_service.update_template_metadata(template_id, update_data, user_id)
    
    assert result is not None
    assert result["name"] == "Updated Template Name"
    assert result["description"] == "Updated description"
    assert result["status"] == "active"


@pytest.mark.asyncio
async def test_create_template_version(template_service):
    """Test creating a new template version"""
    template_id = uuid.uuid4()
    version_data = TemplateVersionCreate(
        version_notes="Updated version with new sections",
        template_data={"updated": "data"}
    )
    
    mock_version_row = {
        "id": uuid.uuid4(),
        "template_id": template_id,
        "version_number": "1.1",
        "version_notes": "Updated version with new sections",
        "status": "active",
        "created_by": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_by": uuid.uuid4(),
        "updated_at": datetime.utcnow()
    }
    
    mock_conn = template_service.db_pool.acquire.return_value.__aenter__.return_value
    mock_conn.fetchrow.return_value = mock_version_row
    mock_conn.execute.return_value = None
    
    user_id = uuid.uuid4()
    result = await template_service.create_template_version(template_id, version_data, user_id)
    
    assert result is not None
    assert result["version_number"] == "1.1"
    assert result["version_notes"] == "Updated version with new sections"


@pytest.mark.asyncio
async def test_get_all_templates(template_service):
    """Test getting all templates"""
    mock_rows = [
        {
            "id": uuid.uuid4(),
            "name": "Template 1",
            "filename": "template1.json",
            "template_type": "proposal",
            "description": "Description 1",
            "status": "active",
            "is_default": True,
            "created_by": uuid.uuid4(),
            "created_at": datetime.utcnow(),
            "updated_by": uuid.uuid4(),
            "updated_at": datetime.utcnow(),
            "latest_version": "1.0",
            "latest_version_status": "active",
            "donor_count": 2
        },
        {
            "id": uuid.uuid4(),
            "name": "Template 2",
            "filename": "template2.json",
            "template_type": "concept_note",
            "description": "Description 2",
            "status": "draft",
            "is_default": False,
            "created_by": uuid.uuid4(),
            "created_at": datetime.utcnow(),
            "updated_by": uuid.uuid4(),
            "updated_at": datetime.utcnow(),
            "latest_version": "1.0",
            "latest_version_status": "draft",
            "donor_count": 0
        }
    ]
    
    template_service.db_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = mock_rows
    
    result = await template_service.get_all_templates()
    
    assert result is not None
    assert len(result) == 2
    assert result[0]["name"] == "Template 1"
    assert result[1]["name"] == "Template 2"


@pytest.mark.asyncio
async def test_get_template_donors(template_service):
    """Test getting donors for a template"""
    template_id = uuid.uuid4()
    
    mock_rows = [
        {
            "id": uuid.uuid4(),
            "name": "Donor 1",
            "account_id": "DONOR1",
            "donor_group": "Private Foundation"
        },
        {
            "id": uuid.uuid4(),
            "name": "Donor 2",
            "account_id": "DONOR2",
            "donor_group": "Government"
        }
    ]
    
    template_service.db_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = mock_rows
    
    result = await template_service.get_template_donors(template_id)
    
    assert result is not None
    assert len(result) == 2
    assert result[0]["name"] == "Donor 1"
    assert result[1]["name"] == "Donor 2"


# Test the config.py template loading functions
@patch('backend.core.config.TemplateService')
def test_load_proposal_template_db_fallback(mock_template_service):
    """Test that template loading falls back to file system when DB fails"""
    from backend.core.config import load_proposal_template
    
    # Mock the database service to return None
    mock_service_instance = MagicMock()
    mock_service_instance.get_template_by_filename.return_value = None
    mock_template_service.return_value = mock_service_instance
    
    # Mock file system functions
    with patch('backend.core.config._find_template_path') as mock_find_path, \
         patch('builtins.open', create=True) as mock_open, \
         patch('json.load') as mock_json_load:
        
        # Setup mocks
        mock_find_path.return_value = "/path/to/template.json"
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_json_load.return_value = {"test": "template"}
        
        # Call the function
        result = load_proposal_template("test.json")
        
        # Verify it fell back to file system
        mock_find_path.assert_called_once_with("test.json")
        mock_open.assert_called_once_with("/path/to/template.json", "r", encoding="utf-8")
        assert result == {"test": "template"}


@patch('backend.core.config.TemplateService')
def test_load_proposal_template_db_success(mock_template_service):
    """Test that template loading uses DB when available"""
    from backend.core.config import load_proposal_template
    
    # Mock the database service to return template data
    mock_service_instance = MagicMock()
    mock_service_instance.get_template_by_filename.return_value = {
        "template_data": {"db": "template"}
    }
    mock_template_service.return_value = mock_service_instance
    
    # Call the function
    result = load_proposal_template("test.json")
    
    # Verify it used DB
    mock_service_instance.get_template_by_filename.assert_called_once_with("test.json")
    assert result == {"db": "template"}
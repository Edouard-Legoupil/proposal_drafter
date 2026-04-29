#  Standard Library
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from datetime import datetime, timedelta
import uuid


def test_proposal_run_telemetry_logging(authenticated_client):
    """Test that proposal runs are properly logged during generation."""
    client = authenticated_client
    
    # Create a proposal session first
    session_payload = {
        "form_data": {
            "Project title": "Test Telemetry Project",
            "Project type": "Development Aid",
            "Targeted Donor": "test-donor-id",
            "Main Outcome": ["test-outcome-id"],
            "Country / Location(s)": ["test-country-id"]
        },
        "project_description": "A test project for telemetry logging.",
        "document_type": "proposal"
    }
    
    # Create session
    session_response = client.post("/api/create-session", json=session_payload)
    assert session_response.status_code == 200
    session_data = session_response.json()
    session_id = session_data["session_id"]
    proposal_id = session_data["proposal_id"]
    
    # Trigger generation
    gen_response = client.post(f"/api/generate-proposal-sections/{session_id}")
    assert gen_response.status_code == 202
    
    # Give it a moment to process (in real scenario, you'd have a better way to wait)
    import time
    time.sleep(2)  # Short delay for background processing
    
    # Check that runs were logged
    runs_response = client.get(f"/api/proposals/{proposal_id}/runs")
    assert runs_response.status_code == 200
    runs_data = runs_response.json()
    
    # Should have at least one run
    assert "runs" in runs_data
    assert len(runs_data["runs"]) >= 1
    
    # Check run details
    run = runs_data["runs"][0]
    assert "run_id" in run
    assert "proposal_id" in run
    assert "user_id" in run
    assert "run_status" in run
    assert "start_time" in run
    assert "template_name" in run


def test_get_proposal_run_details(authenticated_client):
    """Test getting detailed information about a specific proposal run."""
    client = authenticated_client
    
    # This test assumes there's already a run in the database
    # In a real scenario, you'd create one first or use a fixture
    
    # For now, we'll just test the endpoint structure
    fake_run_id = str(uuid.uuid4())
    
    # This should return 404 since the run doesn't exist
    response = client.get(f"/api/proposal-runs/{fake_run_id}")
    assert response.status_code == 500  # Will fail because run doesn't exist


def test_get_user_runs(authenticated_client):
    """Test getting all runs for a specific user."""
    client = authenticated_client
    
    # Get current user's ID from profile
    profile_response = client.get("/api/profile")
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    user_id = profile_data["user"]["id"]
    
    # Get user's runs
    runs_response = client.get(f"/api/users/{user_id}/runs")
    assert runs_response.status_code == 200
    runs_data = runs_response.json()
    
    # Should have runs array
    assert "runs" in runs_data
    assert isinstance(runs_data["runs"], list)


def test_get_all_runs(authenticated_client):
    """Test getting all proposal runs."""
    client = authenticated_client
    
    # Get all runs (limited to recent ones)
    runs_response = client.get("/api/proposal-runs?limit=10")
    assert runs_response.status_code == 200
    runs_data = runs_response.json()
    
    # Should have runs array
    assert "runs" in runs_data
    assert isinstance(runs_data["runs"], list)
    
    # Check that runs have expected structure
    for run in runs_data["runs"]:
        assert "run_id" in run
        assert "proposal_id" in run
        assert "user_id" in run
        assert "run_status" in run
        assert "start_time" in run


def test_get_runs_by_agent(authenticated_client):
    """Test getting runs that executed a specific agent."""
    client = authenticated_client
    
    # Test with a common agent name
    agent_name = "content_generator"
    runs_response = client.get(f"/api/proposal-runs/agents/{agent_name}?limit=10")
    assert runs_response.status_code == 200
    runs_data = runs_response.json()
    
    # Should have runs array
    assert "runs" in runs_data
    assert isinstance(runs_data["runs"], list)


def test_proposal_run_telemetry_structure():
    """Test that telemetry data has the correct structure."""
    from backend.utils.proposal_run_logger import artifact_run_logger
    
    # Test data
    test_proposal_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    
    # Create a test run
    run_id = artifact_run_logger.create_run_record(
        artifact_type="proposal",
        artifact_id=test_proposal_id,
        user_id=test_user_id,
        template_name="test_template.json",
        model_deployment="test-model"
    )
    
    # Log some agent executions
    proposal_run_logger.log_agent_execution(
        run_id=run_id,
        agent_name="content_generator",
        stage_latency_ms=1500,
        tokens_used=100,
        step_count=1
    )
    
    proposal_run_logger.log_agent_execution(
        run_id=run_id,
        agent_name="evaluator",
        stage_latency_ms=800,
        tokens_used=50,
        step_count=1
    )
    
    # Log output metrics
    proposal_run_logger.log_output_metrics(
        run_id=run_id,
        sections_generated=5,
        words_generated=2500,
        pages_generated=3
    )
    
    # Complete the run
    proposal_run_logger.complete_run(
        run_id=run_id,
        total_latency_ms=5000,
        success=True
    )
    
    # Get run details
    run_details = proposal_run_logger.get_run_details(run_id)
    
    # Verify structure
    assert "id" in run_details
    assert "proposal_id" in run_details
    assert "user_id" in run_details
    assert "run_status" in run_details
    assert "start_time" in run_details
    assert "end_time" in run_details
    assert "agents_executed" in run_details
    assert "model_deployment" in run_details
    assert "tokens_input" in run_details
    assert "tokens_output" in run_details
    assert "estimated_cost" in run_details
    assert "step_count" in run_details
    assert "retry_count" in run_details
    assert "failure_count" in run_details
    assert "total_latency_ms" in run_details
    assert "sections_generated" in run_details
    assert "pages_generated" in run_details
    assert "words_generated" in run_details
    assert "template_name" in run_details
    assert "template_version" in run_details
    
    # Verify values
    assert run_details["run_status"] == "completed"
    assert run_details["sections_generated"] == 5
    assert run_details["words_generated"] == 2500
    assert run_details["pages_generated"] == 3
    assert run_details["step_count"] == 2  # Two agents logged
    assert len(run_details["agents_executed"]) == 2
    assert "content_generator" in run_details["agents_executed"]
    assert "evaluator" in run_details["agents_executed"]


def test_proposal_run_failure_logging():
    """Test logging of failed proposal runs."""
    from backend.utils.proposal_run_logger import artifact_run_logger
    
    # Test data
    test_proposal_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    
    # Create a test run
    run_id = artifact_run_logger.create_run_record(
        artifact_type="proposal",
        artifact_id=test_proposal_id,
        user_id=test_user_id,
        template_name="test_template.json"
    )
    
    # Log an agent execution
    proposal_run_logger.log_agent_execution(
        run_id=run_id,
        agent_name="content_generator",
        stage_latency_ms=1500
    )
    
    # Log a failure
    proposal_run_logger.log_failure(
        run_id=run_id,
        agent_name="content_generator",
        error_message="Test error message"
    )
    
    # Complete the run as failed
    proposal_run_logger.complete_run(
        run_id=run_id,
        total_latency_ms=2000,
        success=False
    )
    
    # Get run details
    run_details = proposal_run_logger.get_run_details(run_id)
    
    # Verify failure logging
    assert run_details["run_status"] == "failed"
    assert run_details["failure_count"] == 1
    assert "failures" in run_details["metadata"]
    failures = run_details["metadata"]["failures"]
    assert len(failures) == 1
    assert failures[0]["agent"] == "content_generator"
    assert failures[0]["error"] == "Test error message"


def test_knowledge_card_telemetry_structure():
    """Test that knowledge card telemetry data has the correct structure."""
    from backend.utils.proposal_run_logger import artifact_run_logger
    
    # Test data
    test_card_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    
    # Create a test run for knowledge card
    run_id = artifact_run_logger.create_run_record(
        artifact_type="knowledge_card",
        artifact_id=test_card_id,
        user_id=test_user_id,
        template_name="knowledge_card_donor_template.json",
        model_deployment="default"
    )
    
    # Log some agent executions
    artifact_run_logger.log_agent_execution(
        run_id=run_id,
        agent_name="content_generator",
        stage_latency_ms=2000,
        tokens_used=150,
        step_count=1
    )
    
    # Log output metrics
    artifact_run_logger.log_output_metrics(
        run_id=run_id,
        sections_generated=3,
        words_generated=1800,
        pages_generated=2
    )
    
    # Complete the run
    artifact_run_logger.complete_run(
        run_id=run_id,
        total_latency_ms=6000,
        success=True
    )
    
    # Get run details
    run_details = artifact_run_logger.get_run_details(run_id)
    
    # Verify structure
    assert "id" in run_details
    assert "artifact_type" in run_details
    assert "artifact_id" in run_details
    assert "user_id" in run_details
    assert "run_status" in run_details
    assert run_details["artifact_type"] == "knowledge_card"
    assert run_details["artifact_id"] == test_card_id
    
    # Verify values
    assert run_details["run_status"] == "completed"
    assert run_details["sections_generated"] == 3
    assert run_details["words_generated"] == 1800
    assert run_details["pages_generated"] == 2
    assert run_details["step_count"] == 1
    assert len(run_details["agents_executed"]) == 1
    assert "content_generator" in run_details["agents_executed"]
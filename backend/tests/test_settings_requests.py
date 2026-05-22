# Standard Library
import pytest
import uuid
from sqlalchemy import text


def test_settings_request_workflow(test_engine):
    """Test the complete settings request workflow"""
    with test_engine.connect() as connection:
        # Setup: Create test data
        connection.execute(
            text("INSERT INTO donors (id, name) VALUES ('donor-1', 'Test Donor 1')")
        )
        connection.execute(
            text("INSERT INTO outcomes (id, name) VALUES ('outcome-1', 'Test Outcome 1')")
        )
        connection.execute(
            text("INSERT INTO field_contexts (id, name) VALUES ('field-1', 'Test Field Context 1')")
        )
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES ('team-1', 'Test Team 1')")
        )
        
        # Create test user
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, 'test@example.com', 'password', 'Test User')"),
            {'id': user_id}
        )
        
        # Test 1: User can request donor focal
        connection.execute(
            text("""
            INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
            VALUES (:user_id, 'donor_focal', 'donor-1', 'pending')
            """),
            {'user_id': user_id}
        )
        
        # Verify request was stored
        result = connection.execute(
            text("SELECT setting_type, setting_value, status FROM user_settings_requests WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        assert result[0] == 'donor_focal'
        assert result[1] == 'donor-1'
        assert result[2] == 'pending'
        
        # Test 2: Admin can approve the request
        connection.execute(
            text("INSERT INTO user_donors (user_id, donor_id) VALUES (:user_id, 'donor-1')"),
            {'user_id': user_id}
        )
        connection.execute(
            text("""
            UPDATE user_settings_requests
            SET status = 'approved'
            WHERE user_id = :user_id AND setting_type = 'donor_focal'
            """),
            {'user_id': user_id}
        )
        
        # Verify setting was granted
        result = connection.execute(
            text("SELECT donor_id FROM user_donors WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        assert result[0] == 'donor-1'
        
        # Test 3: User can request outcome focal
        connection.execute(
            text("""
            INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
            VALUES (:user_id, 'outcome_focal', 'outcome-1', 'pending')
            """),
            {'user_id': user_id}
        )
        
        # Test 4: User can request field context focal
        connection.execute(
            text("""
            INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
            VALUES (:user_id, 'field_context_focal', 'field-1', 'pending')
            """),
            {'user_id': user_id}
        )
        
        # Test 5: User can request team membership
        connection.execute(
            text("""
            INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
            VALUES (:user_id, 'team_membership', 'team-1', 'pending')
            """),
            {'user_id': user_id}
        )
        
        # Test 6: User cannot request the same setting twice
        with pytest.raises(Exception):
            connection.execute(
                text("""
                INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
                VALUES (:user_id, 'donor_focal', 'donor-1', 'pending')
                """),
                {'user_id': user_id}
            )


def test_settings_validation(test_engine):
    """Test settings request validation"""
    with test_engine.connect() as connection:
        # Setup: Create test data
        connection.execute(
            text("INSERT INTO donors (id, name) VALUES ('donor-1', 'Test Donor 1')")
        )
        
        # Create test user
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, 'test@example.com', 'password', 'Test User')"),
            {'id': user_id}
        )
        
        # User already has the donor
        connection.execute(
            text("INSERT INTO user_donors (user_id, donor_id) VALUES (:user_id, 'donor-1')"),
            {'user_id': user_id}
        )
        
        # Should not be able to request the same donor
        with pytest.raises(Exception):
            connection.execute(
                text("""
                INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
                VALUES (:user_id, 'donor_focal', 'donor-1', 'pending')
                """),
                {'user_id': user_id}
            )


def test_admin_settings_management(test_engine):
    """Test admin settings management functions"""
    with test_engine.connect() as connection:
        # Setup: Create test data
        connection.execute(
            text("INSERT INTO donors (id, name) VALUES ('donor-1', 'Test Donor 1')")
        )
        
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, 'test@example.com', 'password', 'Test User')"),
            {'id': user_id}
        )
        
        # User requests a donor
        connection.execute(
            text("""
            INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
            VALUES (:user_id, 'donor_focal', 'donor-1', 'pending')
            """),
            {'user_id': user_id}
        )
        
        # Admin can see the request
        result = connection.execute(
            text("""
            SELECT u.email, usr.setting_type, usr.setting_value
            FROM user_settings_requests usr
            JOIN users u ON usr.user_id = u.id
            WHERE usr.user_id = :user_id AND usr.status = 'pending'
            """),
            {'user_id': user_id}
        ).fetchone()
        
        assert result[0] == 'test@example.com'
        assert result[1] == 'donor_focal'
        assert result[2] == 'donor-1'
        
        # Admin can approve the request
        connection.execute(
            text("INSERT INTO user_donors (user_id, donor_id) VALUES (:user_id, 'donor-1')"),
            {'user_id': user_id}
        )
        connection.execute(
            text("""
            UPDATE user_settings_requests
            SET status = 'approved'
            WHERE user_id = :user_id AND setting_type = 'donor_focal'
            """),
            {'user_id': user_id}
        )
        
        # Verify donor was granted
        result = connection.execute(
            text("SELECT donor_id FROM user_donors WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        assert result[0] == 'donor-1'
        
        # Admin can reject requests
        connection.execute(
            text("""
            INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
            VALUES (:user_id, 'outcome_focal', 'outcome-1', 'pending')
            """),
            {'user_id': user_id}
        )
        
        connection.execute(
            text("""
            UPDATE user_settings_requests
            SET status = 'rejected', rejection_reason = 'Not needed'
            WHERE user_id = :user_id AND setting_type = 'outcome_focal'
            """),
            {'user_id': user_id}
        )
        
        # Verify outcome was not granted
        result = connection.execute(
            text("SELECT outcome_id FROM user_outcomes WHERE user_id = :user_id"),
            {'user_id': user_id}
        ).fetchone()
        
        assert result is None


def test_settings_request_types(test_engine):
    """Test all supported setting request types"""
    with test_engine.connect() as connection:
        # Setup: Create test data
        connection.execute(
            text("INSERT INTO donors (id, name) VALUES ('donor-1', 'Test Donor')")
        )
        connection.execute(
            text("INSERT INTO outcomes (id, name) VALUES ('outcome-1', 'Test Outcome')")
        )
        connection.execute(
            text("INSERT INTO field_contexts (id, name) VALUES ('field-1', 'Test Field Context')")
        )
        connection.execute(
            text("INSERT INTO teams (id, name) VALUES ('team-1', 'Test Team')")
        )
        
        user_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO users (id, email, password, name) VALUES (:id, 'test@example.com', 'password', 'Test User')"),
            {'id': user_id}
        )
        
        # Test all setting types
        setting_types = [
            ('donor_focal', 'donor-1'),
            ('outcome_focal', 'outcome-1'),
            ('field_context_focal', 'field-1'),
            ('team_membership', 'team-1')
        ]
        
        for setting_type, setting_value in setting_types:
            connection.execute(
                text("""
                INSERT INTO user_settings_requests (user_id, setting_type, setting_value, status)
                VALUES (:user_id, :setting_type, :setting_value, 'pending')
                """),
                {'user_id': user_id, 'setting_type': setting_type, 'setting_value': setting_value}
            )
            
            # Verify each request was stored
            result = connection.execute(
                text("""
                SELECT setting_type, setting_value, status FROM user_settings_requests
                WHERE user_id = :user_id AND setting_type = :setting_type
                """),
                {'user_id': user_id, 'setting_type': setting_type}
            ).fetchone()
            
            assert result[0] == setting_type
            assert result[1] == setting_value
            assert result[2] == 'pending'
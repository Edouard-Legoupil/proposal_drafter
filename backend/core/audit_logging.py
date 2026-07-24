#  Standard Library
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

#  Third-Party Libraries
from fastapi import Request

#  Internal Modules


class AuditEvent:
    """
    Represents a single audit event with comprehensive security context.

    Attributes:
        event_type: Type of event (e.g., "security.login.success")
        user_id: User associated with the event
        ip_address: IP address of the requester
        user_agent: User agent string
        metadata: Additional event-specific data
        timestamp: When the event occurred
        level: Severity level (INFO, WARNING, ERROR, CRITICAL)
    """

    def __init__(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO",
    ):
        self.event_type = event_type
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)
        self.level = level.upper()

        # Add common security context
        if "security_context" not in self.metadata:
            self.metadata["security_context"] = {"compliance_tags": self._get_compliance_tags()}

    def _get_compliance_tags(self) -> List[str]:
        """Get compliance tags based on event type."""
        tags = []

        if self.event_type.startswith("security."):
            tags.append("ISO27001:A.12.4.1")
            tags.append("NIST:AC-2")
            tags.append("GDPR:Art32")

        if "login" in self.event_type:
            tags.append("ISO27001:A.9.4.2")
            tags.append("NIST:IA-2")

        if "data" in self.event_type:
            tags.append("ISO27001:A.12.1.2")
            tags.append("GDPR:Art30")

        return tags

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self._redact_sensitive_data(self.metadata),
            "level": self.level,
        }

    def _redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from metadata."""
        sensitive_keys = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "api_key",
            "apiKey",
            "access_token",
            "refresh_token",
            "credit_card",
            "card_number",
            "cvv",
            "ssn",
            "authorization",
            "bearer",
            "credentials",
        ]

        redacted = data.copy()
        for key, value in redacted.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive_data(value)

        return redacted


class AuditLogger:
    """
    Comprehensive audit logging system for security and compliance.

    Features:
    - Multiple event types (security, API calls, data access, system)
    - Sensitive data redaction
    - Log rotation and retention
    - Search and analysis capabilities
    - Compliance reporting
    - Threshold-based alerts
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        max_log_size: int = 10 * 1024 * 1024,  # 10MB
        max_log_files: int = 5,
        failed_login_threshold: int = 5,
    ):
        self.log_file: str = log_file or os.getenv("AUDIT_LOG_FILE") or "audit.log"
        self.max_log_size = max_log_size
        self.max_log_files = max_log_files
        self.failed_login_threshold = failed_login_threshold
        self.log_events: List[AuditEvent] = []
        self.security_events: List[AuditEvent] = []
        self.failed_login_attempts: Dict[str, List[AuditEvent]] = {}
        self.lock = threading.Lock()

        # Ensure log directory exists if log_file is a path
        log_dir = os.path.dirname(self.log_file) or "."
        os.makedirs(log_dir, exist_ok=True)

        # Initialize logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup basic logging configuration."""
        self.logger = logging.getLogger("audit_logger")
        self.logger.setLevel(logging.INFO)

        # Create file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add handler if not already present
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def _write_log(self, log_entry: str):
        """Write log entry to file with rotation."""
        try:
            # Check if log file needs rotation
            if os.path.exists(self.log_file):
                file_size = os.path.getsize(self.log_file)
                if file_size > self.max_log_size:
                    self._rotate_logs()

            # Write to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")

        except Exception as e:
            # Fallback to console logging if file write fails
            print(f"Audit log write failed: {e}")
            print(f"Log entry: {log_entry}")

    def _rotate_logs(self):
        """Rotate log files to prevent disk space issues."""
        try:
            # Close current file handler
            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    self.logger.removeHandler(handler)

            # Rename existing logs
            for i in range(self.max_log_files - 1, 0, -1):
                prev_file = f"{self.log_file}.{i}"
                new_file = f"{self.log_file}.{i + 1}"
                if os.path.exists(prev_file):
                    if os.path.exists(new_file):
                        os.remove(new_file)
                    os.rename(prev_file, new_file)

            # Rename current log
            if os.path.exists(self.log_file):
                os.rename(self.log_file, f"{self.log_file}.1")

            # Reopen log file
            self._setup_logging()

        except Exception as e:
            print(f"Log rotation failed: {e}")

    def log_security_event(
        self,
        user_id: Optional[str],
        event_type: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log security-related events (logins, authorization, etc.).

        Args:
            user_id: User ID associated with the event
            event_type: Type of security event
            success: Whether the event was successful
            ip_address: IP address of the requester
            user_agent: User agent string
            metadata: Additional event data
        """
        # Prepend security prefix if not present
        if not event_type.startswith("security."):
            event_type = f"security.{event_type}"

        # Add success status to metadata
        if metadata is None:
            metadata = {}
        metadata["success"] = success

        # Create and store event
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            level="WARNING" if not success else "INFO",
        )

        alert_message = None
        with self.lock:
            self.log_events.append(event)
            self.security_events.append(event)

            # Track failed login attempts for brute force detection
            if not success and "login" in event_type:
                failure_key = user_id or "<unknown>"
                if failure_key not in self.failed_login_attempts:
                    self.failed_login_attempts[failure_key] = []
                self.failed_login_attempts[failure_key].append(event)

                # Check threshold
                if len(self.failed_login_attempts[failure_key]) >= self.failed_login_threshold:
                    alert_message = f"Brute force attempt detected for user {user_id}"

        # Alert handling records another event and must run after releasing self.lock.
        if alert_message:
            self._trigger_alert(alert_message)

        # Write to log file
        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def log_api_call(
        self,
        user_id: Optional[str],
        endpoint: str,
        method: str,
        status_code: int = 200,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log API calls for monitoring and compliance.

        Args:
            user_id: User ID making the API call
            endpoint: API endpoint called
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            ip_address: IP address of the requester
            user_agent: User agent string
            response_time_ms: Response time in milliseconds
            metadata: Additional call data
        """
        if metadata is None:
            metadata = {}

        metadata.update(
            {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
            }
        )

        event = AuditEvent(
            event_type=f"api.call.{method.lower()}",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            level="ERROR" if status_code >= 500 else "INFO",
        )

        with self.lock:
            self.log_events.append(event)

        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def log_data_access(
        self,
        user_id: Optional[str],
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log data access events for compliance and monitoring.

        Args:
            user_id: User ID accessing the data
            resource_type: Type of resource (proposal, user, etc.)
            resource_id: ID of the resource
            action: Action performed (read, write, delete)
            ip_address: IP address of the requester
            user_agent: User agent string
            metadata: Additional access data
        """
        if metadata is None:
            metadata = {}

        metadata.update(
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
            }
        )

        event = AuditEvent(
            event_type=f"data.access.{action}",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )

        with self.lock:
            self.log_events.append(event)

        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def log_system_event(
        self,
        event_type: str,
        component: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log system-level events (startup, shutdown, errors).

        Args:
            event_type: Type of system event
            component: System component
            status: Event status (success, failure, etc.)
            metadata: Additional event data
        """
        if metadata is None:
            metadata = {}

        metadata.update({"component": component, "status": status})

        event = AuditEvent(
            event_type=f"system.{event_type}",
            user_id="system",
            metadata=metadata,
            level="ERROR" if status == "failure" else "INFO",
        )

        with self.lock:
            self.log_events.append(event)

        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def log_comprehensive_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ):
        """
        Enhanced security event logging with comprehensive context.

        This method provides detailed security logging for ISO 27001 compliance.

        Args:
            event_type: Type of security event (e.g., 'login', 'authorization', 'data_access')
            user_id: User ID associated with the event
            success: Whether the event was successful
            ip_address: IP address of the requester
            user_agent: User agent string
            metadata: Additional event data
            request: Optional FastAPI request object for additional context
        """
        if metadata is None:
            metadata = {}

        # Add request context if available
        if request:
            metadata.update(
                {
                    "request_path": str(request.url.path),
                    "request_method": request.method,
                    "query_params": dict(request.query_params),
                    "headers": self._get_safe_headers(request.headers),
                }
            )

        # Add ISO 27001 compliance tags
        compliance_tags = ["ISO27001:A.12.4.1", "ISO27001:A.12.4.2"]

        if "login" in event_type.lower():
            compliance_tags.extend(["ISO27001:A.9.4.2", "ISO27001:A.9.4.3"])
        elif "authorization" in event_type.lower():
            compliance_tags.extend(["ISO27001:A.9.1.2", "ISO27001:A.9.2.3"])
        elif "data" in event_type.lower():
            compliance_tags.extend(["ISO27001:A.12.1.2", "ISO27001:A.12.5.1"])

        metadata["compliance_tags"] = compliance_tags
        metadata["success"] = success

        # Determine severity level
        severity = "high" if not success else "medium"
        if "brute_force" in metadata.get("threat_type", ""):
            severity = "critical"

        event = AuditEvent(
            event_type=f"security.{event_type}",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            level="ERROR" if severity == "high" else "INFO",
        )

        with self.lock:
            self.log_events.append(event)
            self.security_events.append(event)

            # Check for brute force patterns
            if not success and "login" in event_type.lower():
                self._check_brute_force_pattern(user_id, ip_address)

        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def _check_brute_force_pattern(self, user_id: Optional[str], ip_address: Optional[str]):
        """Check for brute force attack patterns."""
        if not user_id and not ip_address:
            return

        # Simple brute force detection (enhanced version would use time windows)
        recent_failures = []

        for event in reversed(self.security_events[-10:]):  # Check last 10 events
            matches_actor = event.user_id == user_id or (ip_address and event.metadata.get("ip_address") == ip_address)
            if matches_actor and event.event_type == "security.login" and not event.metadata.get("success", True):
                recent_failures.append(event)

        if len(recent_failures) >= 3:
            # Trigger brute force alert
            self._trigger_security_alert(
                "brute_force_detected",
                f"Potential brute force attack detected for user {user_id} from IP {ip_address}",
                {"failed_attempts": len(recent_failures), "user_id": user_id, "ip_address": ip_address},
            )

    def _trigger_security_alert(self, alert_type: str, message: str, context: Dict[str, Any]):
        """Trigger a security alert for immediate attention."""
        alert_event = AuditEvent(
            event_type=f"security.alert.{alert_type}",
            user_id="system",
            metadata={
                "message": message,
                "context": context,
                "compliance_tags": ["ISO27001:A.16.1.2", "ISO27001:A.16.1.5"],
                "alert_severity": "critical",
            },
            level="CRITICAL",
        )

        with self.lock:
            self.log_events.append(alert_event)
            self.security_events.append(alert_event)

        log_entry = json.dumps(alert_event.to_dict())
        self._write_log(log_entry)

        # Also log to console for immediate visibility
        console_message = f"🚨 SECURITY ALERT: {message}"
        print(console_message)
        logging.critical(console_message)

    def _get_safe_headers(self, headers) -> Dict[str, str]:
        """Get safe headers for logging (redact sensitive ones)."""
        sensitive_headers = [
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-access-token",
            "proxy-authorization",
        ]

        safe_headers = {}
        for key, value in headers.items():
            if key.lower() not in sensitive_headers:
                safe_headers[key] = value
            else:
                safe_headers[key] = "[REDACTED]"

        return safe_headers

    def log_rate_limit_event(
        self,
        user_id: Optional[str],
        endpoint: str,
        ip_address: Optional[str] = None,
        limit: str = "unknown",
        request: Optional[Request] = None,
    ):
        """Log rate limit events for security monitoring."""
        metadata = {
            "endpoint": endpoint,
            "rate_limit": limit,
            "action": "rate_limit_exceeded",
            "compliance_tags": ["ISO27001:A.12.1.3", "ISO27001:A.13.1.1"],
            "security_context": {"threat_type": "denial_of_service", "mitigation": "rate_limiting"},
        }

        if request:
            metadata["request_path"] = str(request.url.path)
            metadata["request_method"] = request.method

        event = AuditEvent(
            event_type="security.rate_limit_exceeded",
            user_id=user_id,
            ip_address=ip_address,
            metadata=metadata,
            level="WARNING",
        )

        with self.lock:
            self.log_events.append(event)
            self.security_events.append(event)

        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def log_sensitive_data_access(
        self,
        user_id: str,
        data_type: str,
        resource_id: str,
        operation: str,
        justification: str,
        ip_address: Optional[str] = None,
        request: Optional[Request] = None,
    ):
        """Log access to sensitive data with justification."""
        metadata = {
            "data_type": data_type,
            "resource_id": resource_id,
            "operation": operation,
            "justification": justification,
            "compliance_tags": ["ISO27001:A.12.5.1", "GDPR:Art5", "GDPR:Art30"],
            "security_context": {"data_classification": "sensitive", "access_reason": justification},
        }

        if request:
            metadata["request_path"] = str(request.url.path)
            metadata["request_method"] = request.method

        event = AuditEvent(
            event_type="security.sensitive_data_access",
            user_id=user_id,
            ip_address=ip_address,
            metadata=metadata,
            level="INFO",
        )

        with self.lock:
            self.log_events.append(event)
            self.security_events.append(event)

        log_entry = json.dumps(event.to_dict())
        self._write_log(log_entry)

    def generate_security_report(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Generate a comprehensive security report for compliance.

        Args:
            time_range: Time range for the report ('24h', '7d', '30d', 'all')

        Returns:
            Security report with metrics and findings
        """
        from datetime import timedelta

        # Determine time range
        now = datetime.now(timezone.utc)
        if time_range == "24h":
            cutoff = now - timedelta(hours=24)
        elif time_range == "7d":
            cutoff = now - timedelta(days=7)
        elif time_range == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = None

        # Filter events by time range
        if cutoff:
            recent_events = [e for e in self.log_events if e.timestamp >= cutoff]
            recent_security = [e for e in self.security_events if e.timestamp >= cutoff]
        else:
            recent_events = self.log_events
            recent_security = self.security_events

        # Calculate metrics
        total_events = len(recent_events)
        security_events = len(recent_security)

        # Count by event type
        event_types: Dict[str, int] = {}
        for event in recent_events:
            event_type = event.event_type.split(".")[0]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Count security events by type
        security_types: Dict[str, int] = {}
        for event in recent_security:
            sec_type = event.event_type.split(".")[1] if len(event.event_type.split(".")) > 1 else "other"
            security_types[sec_type] = security_types.get(sec_type, 0) + 1

        # Count failed vs successful security events
        failed_security = sum(1 for e in recent_security if not e.metadata.get("success", True))
        successful_security = security_events - failed_security

        # Get unique users
        unique_users = set()
        for event in recent_events:
            if event.user_id and event.user_id != "system":
                unique_users.add(event.user_id)

        # Generate compliance assessment
        compliance_status = "compliant"
        compliance_issues = []

        if security_events == 0:
            compliance_issues.append("No security events logged in the period")
            compliance_status = "pending"

        if failed_security > security_events * 0.1:  # More than 10% failed
            compliance_issues.append(f"High failure rate ({failed_security}/{security_events}) may indicate issues")
            compliance_status = "warning"

        return {
            "report_timestamp": now.isoformat(),
            "time_range": time_range,
            "compliance_status": compliance_status,
            "compliance_issues": compliance_issues,
            "metrics": {
                "total_events": total_events,
                "security_events": security_events,
                "failed_security_events": failed_security,
                "successful_security_events": successful_security,
                "unique_users": len(unique_users),
                "event_types": event_types,
                "security_event_types": security_types,
            },
            "iso_27001_compliance": {
                "A.12.4.1": "compliant" if security_events > 0 else "pending",
                "A.12.4.2": "compliant" if len(unique_users) > 0 else "pending",
                "A.9.4.2": "compliant" if event_types.get("security", 0) > 0 else "pending",
                "A.16.1.2": "compliant" if len(compliance_issues) == 0 else "warning",
            },
            "recommendations": self._generate_recommendations(compliance_status, compliance_issues),
        }

    def _generate_recommendations(self, status: str, issues: List[str]) -> List[str]:
        """Generate security recommendations based on current status."""
        recommendations = []

        if status == "pending":
            recommendations.append("Enable comprehensive security logging across all endpoints")
            recommendations.append("Implement authentication and authorization logging")
            recommendations.append("Set up regular security audit reviews")

        if status == "warning":
            recommendations.append("Investigate high failure rates in security events")
            recommendations.append("Review authentication mechanisms and error handling")
            recommendations.append("Consider implementing additional security controls")

        if any("brute_force" in issue for issue in issues):
            recommendations.append("Review rate limiting configuration")
            recommendations.append("Consider implementing account lockout policies")
            recommendations.append("Enhance monitoring for brute force attempts")

        return recommendations

    def _trigger_alert(self, message: str):
        """Trigger an alert for security events."""
        # In production, this would send to SIEM, email, etc.
        alert_event = AuditEvent(
            event_type="security.alert.triggered",
            user_id="system",
            metadata={"message": message, "alert_type": "brute_force"},
            level="CRITICAL",
        )

        with self.lock:
            self.log_events.append(alert_event)
            self.security_events.append(alert_event)

        log_entry = json.dumps(alert_event.to_dict())
        self._write_log(log_entry)

        # Also log to console for immediate visibility
        print(f"SECURITY ALERT: {message}")

    def search_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        level: Optional[str] = None,
    ) -> List[AuditEvent]:
        """
        Search audit events with various filters.

        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            after: Only events after this timestamp
            before: Only events before this timestamp
            level: Filter by log level

        Returns:
            List of matching audit events
        """
        with self.lock:
            events = self.log_events.copy()

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if event_type:
            events = [e for e in events if event_type.lower() in e.event_type.lower()]

        if after:
            events = [e for e in events if e.timestamp >= after]

        if before:
            events = [e for e in events if e.timestamp <= before]

        if level:
            events = [e for e in events if e.level == level.upper()]

        return events

    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        Generate a compliance report from audit logs.

        Returns:
            Dictionary containing compliance metrics and statistics
        """
        with self.lock:
            total_events = len(self.log_events)
            security_events = len(self.security_events)
            api_calls = len([e for e in self.log_events if e.event_type.startswith("api.")])
            data_access = len([e for e in self.log_events if e.event_type.startswith("data.")])
            system_events = len([e for e in self.log_events if e.event_type.startswith("system.")])

            # Get unique users
            unique_users = set()
            for event in self.log_events:
                if event.user_id and event.user_id != "system":
                    unique_users.add(event.user_id)

            # Get event types
            event_types: Dict[str, int] = {}
            for event in self.log_events:
                event_type = event.event_type.split(".")[0]
                event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events": total_events,
            "security_events": security_events,
            "api_calls": api_calls,
            "data_access": data_access,
            "system_events": system_events,
            "unique_users": len(unique_users),
            "event_types": event_types,
            "compliance_status": "compliant" if security_events > 0 else "pending",
        }

    def export_logs(self, export_path: str):
        """
        Export audit logs to a JSON file for compliance reporting.

        Args:
            export_path: Path to export file
        """
        with self.lock:
            events = [event.to_dict() for event in self.log_events]

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False


def setup_audit_logging(app):
    """
    Setup audit logging middleware for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Create audit logger instance
    audit_logger = AuditLogger()

    # Store in app state for access in routes
    app.state.audit_logger = audit_logger

    # Add middleware for automatic API call logging
    @app.middleware("http")
    async def audit_logging_middleware(request: Request, call_next):
        """Middleware to automatically log API calls."""
        start_time = datetime.now(timezone.utc)

        # Process the request
        response = await call_next(request)

        # Calculate response time
        end_time = datetime.now(timezone.utc)
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Get user ID if available
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("user_id")

        # Log the API call
        audit_logger.log_api_call(
            user_id=user_id,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            ip_address=request.client.host if request.client else None,
            user_agent=str(request.headers.get("user-agent")),
            response_time_ms=response_time_ms,
        )

        return response

    return app


# Convenience functions for easy logging
def log_security_event(
    user_id: Optional[str],
    event_type: str,
    success: bool,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Convenience function for logging security events."""
    logger = getattr(log_security_event, "_audit_logger", None)
    if logger is None:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_security_event(user_id, event_type, success, ip_address, None, metadata)


def log_api_call(
    user_id: Optional[str],
    endpoint: str,
    method: str,
    status_code: int = 200,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Convenience function for logging API calls."""
    if hasattr(log_api_call, "_audit_logger"):
        logger = log_api_call._audit_logger
    else:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_api_call(user_id, endpoint, method, status_code, ip_address, None, None, metadata)


def log_data_access(
    user_id: Optional[str],
    resource_type: str,
    resource_id: str,
    action: str,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Convenience function for logging data access."""
    if hasattr(log_data_access, "_audit_logger"):
        logger = log_data_access._audit_logger
    else:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_data_access(user_id, resource_type, resource_id, action, ip_address, None, metadata)


def log_system_event(
    event_type: str,
    component: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Convenience function for logging system events."""
    if hasattr(log_system_event, "_audit_logger"):
        logger = log_system_event._audit_logger
    else:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_system_event(event_type, component, status, metadata)


def log_comprehensive_security_event(
    event_type: str,
    user_id: Optional[str],
    success: bool,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
):
    """Convenience function for comprehensive security event logging."""
    if hasattr(log_comprehensive_security_event, "_audit_logger"):
        logger = log_comprehensive_security_event._audit_logger
    else:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_comprehensive_security_event(event_type, user_id, success, ip_address, None, metadata, request)


def log_rate_limit_event(
    user_id: Optional[str],
    endpoint: str,
    ip_address: Optional[str] = None,
    limit: str = "unknown",
    request: Optional[Request] = None,
):
    """Convenience function for logging rate limit events."""
    if hasattr(log_rate_limit_event, "_audit_logger"):
        logger = log_rate_limit_event._audit_logger
    else:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_rate_limit_event(user_id, endpoint, ip_address, limit, request)


def log_sensitive_data_access(
    user_id: str,
    data_type: str,
    resource_id: str,
    operation: str,
    justification: str,
    ip_address: Optional[str] = None,
    request: Optional[Request] = None,
):
    """Convenience function for logging sensitive data access."""
    if hasattr(log_sensitive_data_access, "_audit_logger"):
        logger = log_sensitive_data_access._audit_logger
    else:
        from backend.main import app

        logger = app.state.audit_logger if hasattr(app.state, "audit_logger") else None

    if logger:
        logger.log_sensitive_data_access(user_id, data_type, resource_id, operation, justification, ip_address, request)

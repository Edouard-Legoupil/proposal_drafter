#  Standard Library
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

#  Third-Party Libraries
from sqlalchemy import text
import logging

#  Internal Modules
from backend.core.db import get_engine

# Configure logging
logger = logging.getLogger(__name__)


class ArtifactRunLogger:
    """
    Service for logging artifact generation telemetry data.

    This service handles the persistence of detailed telemetry data for each
    artifact (proposal or knowledge card) generation run, including performance
    metrics, token usage, agent execution details, and output statistics.
    """

    def __init__(self):
        self.engine = get_engine()

    def create_run_record(
        self,
        artifact_type: str,
        artifact_id: str,
        user_id: str,
        template_name: str,
        template_version: str = "1.0",
        model_deployment: str = "default",
    ) -> str:
        """
        Create a new artifact run record.

        Args:
            artifact_type: Type of artifact ('proposal' or 'knowledge_card')
            artifact_id: The ID of the artifact being generated
            user_id: The ID of the user initiating the generation
            template_name: The name of the template being used
            template_version: The version of the template
            model_deployment: The model/deployment being used

        Returns:
            The ID of the created run record
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO artifact_runs (
                            id, artifact_type, artifact_id, user_id, run_status, start_time,
                            model_deployment, template_name, template_version,
                            agents_executed, metadata
                        ) VALUES (
                            :id, :artifact_type, :artifact_id, :user_id, :run_status, :start_time,
                            :model_deployment, :template_name, :template_version,
                            :agents_executed, :metadata
                        )
                    """
                    ),
                    {
                        "id": run_id,
                        "artifact_type": artifact_type,
                        "artifact_id": artifact_id,
                        "user_id": user_id,
                        "run_status": "drafting",
                        "start_time": start_time,
                        "model_deployment": model_deployment,
                        "template_name": template_name,
                        "template_version": template_version,
                        "agents_executed": [],
                        "metadata": json.dumps({"initiated_by": "system"}),
                    },
                )

            logger.info(f"Created {artifact_type} run record {run_id} for artifact {artifact_id}")
            return run_id

        except Exception as e:
            logger.error(f"Failed to create {artifact_type} run record: {e}", exc_info=True)
            raise

    def update_run_status(self, run_id: str, status: str, end_time: Optional[datetime] = None) -> None:
        """
        Update the status of an artifact run.

        Args:
            run_id: The ID of the run to update
            status: The new status (completed, failed, cancelled)
            end_time: Optional end time for the run
        """
        try:
            update_data = {
                "status": status,
                "end_time": end_time if end_time else datetime.utcnow(),
            }

            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET run_status = :status,
                            end_time = :end_time,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "status": status,
                        "end_time": update_data["end_time"],
                    },
                )

            logger.info(f"Updated run {run_id} status to {status}")

        except Exception as e:
            logger.error(f"Failed to update run status {run_id}: {e}", exc_info=True)
            raise

    def log_agent_execution(
        self,
        run_id: str,
        agent_name: str,
        stage_latency_ms: int,
        tokens_used: int = 0,
        step_count: int = 1,
    ) -> None:
        """
        Log the execution of an agent during a proposal run.

        Args:
            run_id: The ID of the run
            agent_name: The name of the agent that executed
            stage_latency_ms: The latency for this agent stage in milliseconds
            tokens_used: The number of tokens used by this agent
            step_count: The number of steps taken by this agent
        """
        try:
            with self.engine.begin() as connection:
                # Get current run data
                result = connection.execute(
                    text(
                        """
                        SELECT agents_executed, step_count, retry_count,
                               tokens_input, tokens_output, stage_latencies
                        FROM artifact_runs
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Run {run_id} not found")

                agents_executed = list(result[0]) if result[0] else []
                current_step_count = result[1] if result[1] else 0
                result[2] if result[2] else 0
                result[3] if result[3] else 0
                current_tokens_output = result[4] if result[4] else 0
                stage_latencies = result[5] if result[5] else {}

                # Update arrays and counters
                if agent_name not in agents_executed:
                    agents_executed.append(agent_name)

                current_step_count += step_count
                current_tokens_output += tokens_used

                # Update stage latencies
                stage_latencies[agent_name] = stage_latency_ms

                # Update the run record
                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            agents_executed = :agents_executed,
                            step_count = :step_count,
                            tokens_output = :tokens_output,
                            stage_latencies = :stage_latencies,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "agents_executed": agents_executed,
                        "step_count": current_step_count,
                        "tokens_output": current_tokens_output,
                        "stage_latencies": json.dumps(stage_latencies),
                    },
                )

            logger.debug(f"Logged agent execution for {agent_name} in run {run_id}")

        except Exception as e:
            logger.error(f"Failed to log agent execution for run {run_id}: {e}", exc_info=True)
            raise

    def log_retry(self, run_id: str, agent_name: str, retry_latency_ms: int) -> None:
        """
        Log a retry attempt during a proposal run.

        Args:
            run_id: The ID of the run
            agent_name: The name of the agent that was retried
            retry_latency_ms: The latency for the retry in milliseconds
        """
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT retry_count, stage_latencies
                        FROM artifact_runs
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Run {run_id} not found")

                current_retry_count = result[0] if result[0] else 0
                stage_latencies = result[1] if result[1] else {}

                # Update retry count
                current_retry_count += 1

                # Track retry latency separately
                retry_key = f"{agent_name}_retry_{current_retry_count}"
                stage_latencies[retry_key] = retry_latency_ms

                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            retry_count = :retry_count,
                            stage_latencies = :stage_latencies,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "retry_count": current_retry_count,
                        "stage_latencies": json.dumps(stage_latencies),
                    },
                )

            logger.debug(f"Logged retry {current_retry_count} for {agent_name} in run {run_id}")

        except Exception as e:
            logger.error(f"Failed to log retry for run {run_id}: {e}", exc_info=True)
            raise

    def log_failure(self, run_id: str, agent_name: str, error_message: str) -> None:
        """
        Log a failure during a proposal run.

        Args:
            run_id: The ID of the run
            agent_name: The name of the agent that failed
            error_message: The error message associated with the failure
        """
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT failure_count, metadata
                        FROM artifact_runs
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Run {run_id} not found")

                current_failure_count = result[0] if result[0] else 0
                metadata = result[1] if result[1] else {}

                # Update failure count
                current_failure_count += 1

                # Store failure details in metadata
                failures = metadata.get("failures", [])
                failures.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent": agent_name,
                        "error": error_message,
                    }
                )
                metadata["failures"] = failures

                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            failure_count = :failure_count,
                            metadata = :metadata,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "failure_count": current_failure_count,
                        "metadata": json.dumps(metadata),
                    },
                )

            logger.warning(f"Logged failure for {agent_name} in run {run_id}: {error_message}")

        except Exception as e:
            logger.error(f"Failed to log failure for run {run_id}: {e}", exc_info=True)
            raise

    def log_output_metrics(
        self,
        run_id: str,
        sections_generated: int,
        words_generated: int,
        pages_generated: int = 1,
    ) -> None:
        """
        Log output metrics for a proposal run.

        Args:
            run_id: The ID of the run
            sections_generated: Number of sections generated
            words_generated: Number of words generated
            pages_generated: Number of pages generated
        """
        try:
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            sections_generated = :sections_generated,
                            words_generated = :words_generated,
                            pages_generated = :pages_generated,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "sections_generated": sections_generated,
                        "words_generated": words_generated,
                        "pages_generated": pages_generated,
                    },
                )

            logger.info(
                f"Logged output metrics for run {run_id}: "
                f"{sections_generated} sections, {words_generated} words, {pages_generated} pages"
            )

        except Exception as e:
            logger.error(f"Failed to log output metrics for run {run_id}: {e}", exc_info=True)
            raise

    def log_export_event(
        self,
        run_id: str,
        export_type: str,
        file_size_bytes: int,
        export_metadata: Dict[str, Any],
    ) -> None:
        """
        Log an export event for a proposal run.

        Args:
            run_id: The ID of the run
            export_type: Type of export (e.g., 'word', 'pdf')
            file_size_bytes: Size of the exported file in bytes
            export_metadata: Additional metadata about the export
        """
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT export_events
                        FROM artifact_runs
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Run {run_id} not found")

                export_events = result[0] if result[0] else []

                # Add new export event
                export_event = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": export_type,
                    "file_size_bytes": file_size_bytes,
                    "metadata": export_metadata,
                }
                export_events.append(export_event)

                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            export_events = :export_events,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id, "export_events": json.dumps(export_events)},
                )

            logger.info(f"Logged {export_type} export event for run {run_id}")

        except Exception as e:
            logger.error(f"Failed to log export event for run {run_id}: {e}", exc_info=True)
            raise

    def log_token_usage(self, run_id: str, tokens_input: int, tokens_output: int, estimated_cost: float) -> None:
        """
        Log token usage and cost for a proposal run.

        Args:
            run_id: The ID of the run
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            estimated_cost: Estimated cost of the run
        """
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT tokens_input, tokens_output, estimated_cost
                        FROM artifact_runs
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Run {run_id} not found")

                current_tokens_input = result[0] if result[0] else 0
                current_tokens_output = result[1] if result[1] else 0
                current_estimated_cost = result[2] if result[2] else 0.0

                # Accumulate token usage and cost
                current_tokens_input += tokens_input
                current_tokens_output += tokens_output
                current_estimated_cost += estimated_cost

                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            tokens_input = :tokens_input,
                            tokens_output = :tokens_output,
                            estimated_cost = :estimated_cost,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "tokens_input": current_tokens_input,
                        "tokens_output": current_tokens_output,
                        "estimated_cost": current_estimated_cost,
                    },
                )

            logger.info(
                f"Logged token usage for run {run_id}: "
                f"{tokens_input} input, {tokens_output} output, ${estimated_cost:.4f} cost"
            )

        except Exception as e:
            logger.error(f"Failed to log token usage for run {run_id}: {e}", exc_info=True)
            raise

    def complete_run(self, run_id: str, total_latency_ms: int, success: bool = True) -> None:
        """
        Mark a proposal run as completed.

        Args:
            run_id: The ID of the run
            total_latency_ms: Total latency for the run in milliseconds
            success: Whether the run completed successfully
        """
        try:
            status = "completed" if success else "failed"
            end_time = datetime.utcnow()

            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE artifact_runs
                        SET
                            run_status = :status,
                            end_time = :end_time,
                            total_latency_ms = :total_latency_ms,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :run_id
                    """
                    ),
                    {
                        "run_id": run_id,
                        "status": status,
                        "end_time": end_time,
                        "total_latency_ms": total_latency_ms,
                    },
                )

            logger.info(f"Completed run {run_id} with status {status} in {total_latency_ms}ms")

        except Exception as e:
            logger.error(f"Failed to complete run {run_id}: {e}", exc_info=True)
            raise

    def get_run_details(self, run_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a proposal run.

        Args:
            run_id: The ID of the run

        Returns:
            Dictionary containing run details
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT
                            id, proposal_id, user_id, run_status, start_time, end_time,
                            agents_executed, model_deployment, tokens_input, tokens_output,
                            estimated_cost, step_count, retry_count, failure_count,
                            total_latency_ms, sections_generated, pages_generated,
                            words_generated, export_events, template_name, template_version,
                            metadata, created_at, updated_at
                        FROM artifact_runs
                        WHERE id = :run_id
                    """
                    ),
                    {"run_id": run_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Run {run_id} not found")

                # Convert result to dictionary
                columns = [
                    "id",
                    "proposal_id",
                    "user_id",
                    "run_status",
                    "start_time",
                    "end_time",
                    "agents_executed",
                    "model_deployment",
                    "tokens_input",
                    "tokens_output",
                    "estimated_cost",
                    "step_count",
                    "retry_count",
                    "failure_count",
                    "total_latency_ms",
                    "sections_generated",
                    "pages_generated",
                    "words_generated",
                    "export_events",
                    "template_name",
                    "template_version",
                    "metadata",
                    "created_at",
                    "updated_at",
                ]

                run_data = dict(zip(columns, result))

                # Convert datetime objects to ISO format strings
                for key in ["start_time", "end_time", "created_at", "updated_at"]:
                    if run_data[key] and isinstance(run_data[key], datetime):
                        run_data[key] = run_data[key].isoformat()

                return run_data

        except Exception as e:
            logger.error(f"Failed to get run details for {run_id}: {e}", exc_info=True)
            raise

    def get_runs_by_artifact(self, artifact_type: str, artifact_id: str) -> List[Dict[str, Any]]:
        """
        Get all runs for a specific artifact (proposal or knowledge card).

        Args:
            artifact_type: Type of artifact ('proposal' or 'knowledge_card')
            artifact_id: The ID of the artifact

        Returns:
            List of run dictionaries
        """
        try:
            with self.engine.connect() as connection:
                results = connection.execute(
                    text(
                        """
                        SELECT
                            id, artifact_type, artifact_id, user_id, run_status, start_time, end_time,
                            agents_executed, model_deployment, tokens_input, tokens_output,
                            estimated_cost, step_count, retry_count, failure_count,
                            total_latency_ms, sections_generated, pages_generated,
                            words_generated, template_name, template_version
                        FROM artifact_runs
                        WHERE artifact_type = :artifact_type AND artifact_id = :artifact_id
                        ORDER BY start_time DESC
                    """
                    ),
                    {"artifact_type": artifact_type, "artifact_id": artifact_id},
                ).fetchall()

                runs = []
                columns = [
                    "id",
                    "artifact_type",
                    "artifact_id",
                    "user_id",
                    "run_status",
                    "start_time",
                    "end_time",
                    "agents_executed",
                    "model_deployment",
                    "tokens_input",
                    "tokens_output",
                    "estimated_cost",
                    "step_count",
                    "retry_count",
                    "failure_count",
                    "total_latency_ms",
                    "sections_generated",
                    "pages_generated",
                    "words_generated",
                    "template_name",
                    "template_version",
                ]

                for result in results:
                    run_data = dict(zip(columns, result))

                    # Convert datetime objects to ISO format strings
                    for key in ["start_time", "end_time"]:
                        if run_data[key] and isinstance(run_data[key], datetime):
                            run_data[key] = run_data[key].isoformat()

                    runs.append(run_data)

                return runs

        except Exception as e:
            logger.error(
                f"Failed to get runs for {artifact_type} {artifact_id}: {e}",
                exc_info=True,
            )
            raise

    def get_runs_by_user(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent runs for a specific user.

        Args:
            user_id: The ID of the user
            limit: Maximum number of runs to return

        Returns:
            List of run dictionaries
        """
        try:
            with self.engine.connect() as connection:
                results = connection.execute(
                    text(
                        """
                        SELECT
                            id, artifact_type, artifact_id, user_id, run_status, start_time, end_time,
                            agents_executed, model_deployment, tokens_input, tokens_output,
                            estimated_cost, step_count, retry_count, failure_count,
                            total_latency_ms, sections_generated, pages_generated,
                            words_generated, template_name, template_version
                        FROM artifact_runs
                        WHERE user_id = :user_id
                        ORDER BY start_time DESC
                        LIMIT :limit
                    """
                    ),
                    {"user_id": user_id, "limit": limit},
                ).fetchall()

                runs = []
                columns = [
                    "id",
                    "artifact_type",
                    "artifact_id",
                    "user_id",
                    "run_status",
                    "start_time",
                    "end_time",
                    "agents_executed",
                    "model_deployment",
                    "tokens_input",
                    "tokens_output",
                    "estimated_cost",
                    "step_count",
                    "retry_count",
                    "failure_count",
                    "total_latency_ms",
                    "sections_generated",
                    "pages_generated",
                    "words_generated",
                    "template_name",
                    "template_version",
                ]

                for result in results:
                    run_data = dict(zip(columns, result))

                    # Convert datetime objects to ISO format strings
                    for key in ["start_time", "end_time"]:
                        if run_data[key] and isinstance(run_data[key], datetime):
                            run_data[key] = run_data[key].isoformat()

                    runs.append(run_data)

                return runs

        except Exception as e:
            logger.error(f"[GET USER RUNS ERROR] {e}", exc_info=True)
            raise

    def get_runs_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get runs within a specific date range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            limit: Maximum number of runs to return

        Returns:
            List of run dictionaries
        """
        try:
            with self.engine.connect() as connection:
                results = connection.execute(
                    text(
                        """
                        SELECT
                            id, proposal_id, user_id, run_status, start_time, end_time,
                            agents_executed, model_deployment, tokens_input, tokens_output,
                            estimated_cost, step_count, retry_count, failure_count,
                            total_latency_ms, sections_generated, pages_generated,
                            words_generated, template_name, template_version
                        FROM artifact_runs
                        WHERE start_time BETWEEN :start_date AND :end_date
                        ORDER BY start_time DESC
                        LIMIT :limit
                    """
                    ),
                    {"start_date": start_date, "end_date": end_date, "limit": limit},
                ).fetchall()

                runs = []
                columns = [
                    "id",
                    "proposal_id",
                    "user_id",
                    "run_status",
                    "start_time",
                    "end_time",
                    "agents_executed",
                    "model_deployment",
                    "tokens_input",
                    "tokens_output",
                    "estimated_cost",
                    "step_count",
                    "retry_count",
                    "failure_count",
                    "total_latency_ms",
                    "sections_generated",
                    "pages_generated",
                    "words_generated",
                    "template_name",
                    "template_version",
                ]

                for result in results:
                    run_data = dict(zip(columns, result))

                    # Convert datetime objects to ISO format strings
                    for key in ["start_time", "end_time"]:
                        if run_data[key] and isinstance(run_data[key], datetime):
                            run_data[key] = run_data[key].isoformat()

                    runs.append(run_data)

                return runs

        except Exception as e:
            logger.error(f"Failed to get runs by date range: {e}", exc_info=True)
            raise

    def get_runs_by_agent(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get runs that executed a specific agent.

        Args:
            agent_name: The name of the agent
            limit: Maximum number of runs to return

        Returns:
            List of run dictionaries
        """
        try:
            with self.engine.connect() as connection:
                results = connection.execute(
                    text(
                        """
                        SELECT
                            id, proposal_id, user_id, run_status, start_time, end_time,
                            agents_executed, model_deployment, tokens_input, tokens_output,
                            estimated_cost, step_count, retry_count, failure_count,
                            total_latency_ms, sections_generated, pages_generated,
                            words_generated, template_name, template_version
                        FROM artifact_runs
                        WHERE :agent_name = ANY(agents_executed)
                        ORDER BY start_time DESC
                        LIMIT :limit
                    """
                    ),
                    {"agent_name": agent_name, "limit": limit},
                ).fetchall()

                runs = []
                columns = [
                    "id",
                    "proposal_id",
                    "user_id",
                    "run_status",
                    "start_time",
                    "end_time",
                    "agents_executed",
                    "model_deployment",
                    "tokens_input",
                    "tokens_output",
                    "estimated_cost",
                    "step_count",
                    "retry_count",
                    "failure_count",
                    "total_latency_ms",
                    "sections_generated",
                    "pages_generated",
                    "words_generated",
                    "template_name",
                    "template_version",
                ]

                for result in results:
                    run_data = dict(zip(columns, result))

                    # Convert datetime objects to ISO format strings
                    for key in ["start_time", "end_time"]:
                        if run_data[key] and isinstance(run_data[key], datetime):
                            run_data[key] = run_data[key].isoformat()

                    runs.append(run_data)

                return runs

        except Exception as e:
            logger.error(f"Failed to get runs by agent {agent_name}: {e}", exc_info=True)
            raise


# Singleton instance for easy access
artifact_run_logger = ArtifactRunLogger()

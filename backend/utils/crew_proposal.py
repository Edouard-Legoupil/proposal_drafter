import logging
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from typing import Dict, Any

from backend.core.llm import llm, get_embedder_config
from backend.utils.prompt_sanitizer import get_prompt_sanitizer
from backend.core.error_handlers import get_error_handler

logger = logging.getLogger(__name__)


@CrewBase
class ProposalCrew:
    """ProposalCrew for generating project proposal"""

    def __init__(self, knowledge_file_paths: list[str] | None = None):
        self.knowledge_file_paths = knowledge_file_paths
        self.json_knowledge = None
        if self.knowledge_file_paths:
            self.json_knowledge = JSONKnowledgeSource(file_paths=self.knowledge_file_paths)
        self.prompt_sanitizer = get_prompt_sanitizer()
        self.error_handler = get_error_handler()

    agents_config: dict[str, Any] = "config/agents_proposal.yaml"  # type: ignore[assignment]
    tasks_config: dict[str, Any] = "config/tasks_proposal.yaml"  # type: ignore[assignment]

    # # Ensure log directory exists
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # log_dir = os.path.join(current_dir, '..', '..', 'logs')
    # os.makedirs(log_dir, exist_ok=True)
    # log_file1 = os.path.join(log_dir, 'log_proposal.txt')
    # log_file2 = os.path.join(log_dir, 'log_proposal_regenerate.txt')

    # generate_proposal_log = log_file1
    # regenerate_proposal_log = log_file2

    def sanitize_task_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize all user-provided inputs to prevent prompt injection.

        Args:
            inputs: Dictionary of task inputs

        Returns:
            Dictionary with sanitized inputs

        Raises:
            HTTPException: If dangerous input is detected
        """
        sanitized_inputs = {}

        for key, value in inputs.items():
            if isinstance(value, str):
                # Sanitize string inputs
                try:
                    sanitization_result = self.prompt_sanitizer.sanitize_user_input(
                        value, context=f"proposal_generation_{key}"
                    )
                    sanitized_inputs[key] = sanitization_result.sanitized_text
                except Exception as e:
                    # If sanitization fails, use a safe default
                    sanitized_inputs[key] = f"[Safe input: {key}]"
                    logger.warning(f"Input sanitization failed for {key}: {e}")
            elif isinstance(value, (int, float, bool)):
                # Pass through numeric and boolean values - convert to string for consistency
                sanitized_inputs[key] = str(value)
            elif isinstance(value, dict):
                # Recursively sanitize dictionaries
                sanitized_inputs[key] = self.sanitize_task_inputs(value)
            elif isinstance(value, list):
                # Sanitize lists
                sanitized_inputs[key] = [self.sanitize_task_inputs({"item": item})["item"] for item in value]
            else:
                # For other types, convert to string and sanitize
                sanitized_inputs[key] = self.prompt_sanitizer.sanitize_user_input(
                    str(value), context=f"proposal_generation_{key}"
                ).sanitized_text

        return sanitized_inputs

    def validate_llm_output(self, output: Any, expected_format: str = "json") -> bool:
        """
        Validate LLM output for security and format compliance.

        Args:
            output: Raw LLM output
            expected_format: Expected format (json, text, etc.)

        Returns:
            True if output is safe and valid, False otherwise

        Raises:
            HTTPException: If output contains suspicious patterns
        """
        if output is None:
            logger.warning("LLM output is None")
            return False

        # Convert to string if needed
        if not isinstance(output, str):
            try:
                if hasattr(output, "model_dump_json"):
                    output = output.model_dump_json()
                elif hasattr(output, "json"):
                    output = output.json()
                else:
                    output = str(output)
            except Exception as e:
                logger.warning(f"Failed to convert LLM output to string: {e}")
                return False

        # Check for suspicious patterns in output
        if not self.prompt_sanitizer.validate_output(output, expected_format):
            logger.warning("LLM output failed security validation")
            security_error = self.error_handler.create_security_error(
                "llm_unavailable", details="LLM output contained suspicious patterns"
            )
            raise security_error

        # Additional validation for JSON format
        if expected_format == "json":
            try:
                import json

                parsed = json.loads(output)

                # Check for required fields
                if "generated_content" not in parsed:
                    logger.warning("LLM output missing required 'generated_content' field")
                    return False

                # Validate content is reasonable
                content = parsed["generated_content"]
                if not content or len(content.strip()) == 0:
                    logger.warning("LLM output 'generated_content' is empty")
                    return False

                # Check for excessive length
                if len(content) > 10000:  # 10k character limit
                    logger.warning(f"LLM output too long: {len(content)} characters")
                    return False

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"LLM output JSON validation failed: {e}")
                return False

        logger.info("LLM output validation passed")
        return True

    ## List of agents ##########
    @agent
    def content_generator(self) -> Agent:
        agent_params = {
            "config": self.agents_config["content_generator"],
            "llm": llm,
            "verbose": True,
        }
        if self.json_knowledge:
            agent_params["knowledge_base"] = self.json_knowledge
        return Agent(**agent_params)

    @agent
    def evaluator(self) -> Agent:
        return Agent(config=self.agents_config["evaluator"], llm=llm, verbose=True)

    @agent
    def regenerator(self) -> Agent:  # ✅ New agent for regeneration
        return Agent(config=self.agents_config["regenerator"], llm=llm, verbose=True)

    ## List of Tasks ##########
    # Task: Generate content for a section
    @task
    def content_generation_task(self) -> Task:
        task_config = self.tasks_config["content_generation_task"]
        return Task(
            description=task_config.get("description", "Generate content for proposal section"),
            expected_output=task_config.get("expected_output", "Generated content for the section"),
            **task_config,
        )

    # Task: Evaluate generated content
    @task
    def evaluation_task(self) -> Task:
        task_config = self.tasks_config["evaluation_task"]
        return Task(
            description=task_config.get("description", "Evaluate generated content"),
            expected_output=task_config.get("expected_output", "Evaluation of the generated content"),
            **task_config,
        )

    # Task: Regenerate content with concise input
    @task
    def regeneration_task(self) -> Task:  # ✅ New task for regeneration
        task_config = self.tasks_config["regeneration_task"]
        return Task(
            description=task_config.get("description", "Regenerate content with concise input"),
            expected_output=task_config.get("expected_output", "Regenerated content for the section"),
            **task_config,
        )

    ## Crew orchestration ####
    @crew
    def generate_proposal_crew(self) -> Crew:  # Ensure method name is correct
        """Creates the ProposalCrew with sequential processing"""
        return Crew(
            agents=[self.content_generator(), self.evaluator()],
            tasks=[self.content_generation_task(), self.evaluation_task()],
            process=Process.sequential,
            verbose=True,
            # output_log_file = self.generate_proposal_log,
            embedder=get_embedder_config(),
        )

    @crew
    def regenerate_proposal_crew(self) -> Crew:  # ✅ New crew for regeneration
        """Creates the ProposalCrew for regenerating a section"""
        return Crew(
            agents=[self.regenerator(), self.evaluator()],
            tasks=[self.regeneration_task(), self.evaluation_task()],
            process=Process.sequential,
            verbose=True,
            # output_log_file = self.regenerate_proposal_log,
            embedder=get_embedder_config(),
        )

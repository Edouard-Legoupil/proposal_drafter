#IOM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
import json
import os
import uuid
from datetime import datetime

from backend.core.llm import llm

@CrewBase
class ProposalCrew():
    """ProposalCrew for generating project proposal"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    generate_proposal_log = 'crew_logs/generate_proposal_log.txt'
    regenerate_proposal_log = 'crew_logs/regenerate_proposal_log.txt'

    # Path to knowledge files
    json_knowledge = JSONKnowledgeSource(
        file_paths=[
            "backend/knowledge/combine_example.json"
        ]
    )

## List of agents ##########
    @agent
    def content_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['content_generator'],
            llm= llm,
            verbose=True
        )

    @agent
    def evaluator(self) -> Agent:
        return Agent(
            config=self.agents_config['evaluator'],
            llm= llm,
            verbose=True
        )

    @agent
    def regenerator(self) -> Agent:  # ✅ New agent for regeneration
        return Agent(
            config=self.agents_config['regenerator'],
            llm= llm,
            verbose=True
        )

## List of Tasks ##########
    # Task: Generate content for a section
    @task
    def content_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_generation_task']
            # inputs={"section": section, "instructions": proposal_data["sections"]}
        )

    # Task: Evaluate generated content
    @task
    def evaluation_task(self) -> Task:
        return Task(
            config=self.tasks_config['evaluation_task']
            # inputs={"section": section, "instructions": proposal_data["sections"]}
        )
    
    # Task: Regenerate content with concise input
    @task
    def regeneration_task(self) -> Task:  # ✅ New task for regeneration
        return Task(
            config=self.tasks_config['regeneration_task']
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
            output_log_file = self.generate_proposal_log,
            embedder={
                "provider": "azure",
                "config": {
                    "model": os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
                    "deployment_id": os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"),
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY_EMBED"),
                    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT_EMBED"),
                    "api_version": os.getenv("AZURE_OPENAI_API_VERSION_EMBED", "2023-05-15")
                }
# # Specify "google" as the provider
#                "provider": "google",  
#                "config": {
#  # Use the Gemini #embedding model
#                    "model": "models/embedding-001", 
# # Optional: #Specify task type for optimized embeddings
#                    "task_type": "retrieval_document", 
#                    "api_key": os.getenv("GEMINI_API_KEY") 
# # Ensure API #key is passed for embedding as well
#                }

            }
        )
       

    @crew
    def regenerate_proposal_crew(self) -> Crew:  # ✅ New crew for regeneration
        """Creates the ProposalCrew for regenerating a section"""
        return Crew(
            agents=[self.regenerator(), self.evaluator()],
            tasks=[self.regeneration_task(), self.evaluation_task()],
            process=Process.sequential,
            verbose=True,
            output_log_file = self.regenerate_proposal_log,
            embedder={
                "provider": "azure",
                "config": {
                    "model": os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
                    "deployment_id": os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"),
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY_EMBED"),
                    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT_EMBED"),
                    "api_version": os.getenv("AZURE_OPENAI_API_VERSION_EMBED", "2023-05-15")
                }
            }
        )
   




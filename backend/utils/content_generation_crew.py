import os
from typing import Type
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
from backend.core.llm import llm, get_embedder_config
from backend.core.db import get_engine
from sqlalchemy import text
import litellm

class VectorSearchTool(BaseTool):
    name: str = "Vector Search"
    description: str = "Searches for relevant information in the knowledge base using vector similarity."

    def _run(self, search_query: str, knowledge_card_id: str) -> str:
        embedder_config = get_embedder_config()["config"]
        model = f"azure/{embedder_config.pop('deployment_id')}"
        embedder_config.pop('model', None)

        response = litellm.embedding(
            model=model,
            input=[search_query],
            **embedder_config
        )
        query_embedding = response.data[0]['embedding']
        with get_engine().connect() as connection:
            # The 1 - (embedding <=> :query_embedding) is for cosine similarity
            # pgvector returns the cosine distance, so we subtract from 1 to get similarity
            query = text("""
                SELECT text_chunk
                FROM knowledge_card_reference_vectors kcrv
                JOIN knowledge_card_references kcr ON kcrv.reference_id = kcr.id
                WHERE kcr.knowledge_card_id = :kc_id
                ORDER BY embedding <=> :query_embedding
                LIMIT 5;
            """)
            results = connection.execute(query, {"kc_id": knowledge_card_id, "query_embedding": str(query_embedding)}).fetchall()
            return "\n".join([row[0] for row in results])

@CrewBase
class ContentGenerationCrew:
    """ContentGenerationCrew for generating knowledge card content"""

    agents_config = 'config/content_generation_agents.yaml'
    tasks_config = 'config/content_generation_tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            tools=[VectorSearchTool()]
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher()
        )

    @task
    def write_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_task'],
            agent=self.writer()
        )

    @crew
    def create_crew(self) -> Crew:
        """Creates the ContentGenerationCrew"""
        return Crew(
            agents=[self.researcher(), self.writer()],
            tasks=[self.research_task(), self.write_task()],
            verbose=True,
            process=Process.sequential,
            output_log_file='log/content_generation.log'
        )

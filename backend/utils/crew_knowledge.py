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
    knowledge_card_id: str = None

    def __init__(self, knowledge_card_id: str):
        super().__init__()
        self.knowledge_card_id = knowledge_card_id

    def _run(self, search_query: str) -> str:
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
            fts_query = " & ".join(search_query.split())
            query = text("""
                SELECT
                    kcrv.text_chunk,
                    kcr.url,
                    (1 - (kcrv.embedding <=> :query_embedding)) * 0.5 +
                    COALESCE(ts_rank(to_tsvector('english', kcrv.text_chunk), to_tsquery('english', :fts_query)), 0) * 0.5 AS hybrid_score
                FROM
                    knowledge_card_reference_vectors kcrv
                JOIN
                    knowledge_card_references kcr ON kcrv.reference_id = kcr.id
                JOIN
                    knowledge_card_to_references kctr ON kcr.id = kctr.reference_id
                WHERE
                    kctr.knowledge_card_id = :kc_id
                ORDER BY
                    hybrid_score DESC
                LIMIT 10;
            """)
            results = connection.execute(query, {
                "kc_id": self.knowledge_card_id,
                "query_embedding": str(query_embedding),
                "fts_query": fts_query
            }).fetchall()
            return "\n\n".join([f"Source: {row[1]}\nChunk: {row[0]}" for row in results])

@CrewBase
class ContentGenerationCrew:
    """ContentGenerationCrew for generating knowledge card content"""
    agents_config = 'config/agents_knowledge.yaml'
    tasks_config = 'config/tasks_knowledge.yaml'
    knowledge_card_id: str = None
    pre_prompt: str = ""

    def __init__(self, knowledge_card_id: str, pre_prompt: str = ""):
        self.knowledge_card_id = knowledge_card_id
        self.pre_prompt = pre_prompt

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            tools=[VectorSearchTool(knowledge_card_id=self.knowledge_card_id)]
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
        research_task_config = self.tasks_config['research_task'].copy()
        research_task_config['description'] = self.pre_prompt + research_task_config['description']
        return Task(
            config=research_task_config,
            agent=self.researcher()
        )

    @task
    def write_task(self) -> Task:
        write_task_config = self.tasks_config['write_task'].copy()
        write_task_config['description'] = self.pre_prompt + write_task_config['description']
        return Task(
            config=write_task_config,
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
            output_log_file='log/log_knowledge.txt'
        )
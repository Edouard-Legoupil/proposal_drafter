import os
from typing import Type
import re
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
from backend.core.llm import llm, get_embedder_config
from backend.core.db import get_engine
from sqlalchemy import text
import litellm

def log_rag_output(output):
    """Callback function to log the final answer of a RAG task."""
    # The raw_output from the tool is passed to the agent, which then forms its answer.
    # The final output of the task will be the agent's answer, not the tool's direct output.
    # We need to parse the log_id from the task's output if it's included,
    # or find a way to access the tool's output from the callback.
    # For now, we assume the agent includes the log_id in its final answer for clarity.

    # A cleaner way would be to pass the log_id through the agent's memory or shared context,
    # but this is a simple approach that works for now.

    # Let's assume the agent is prompted to pass the RAG_LOG_ID through.
    # A more robust solution might be needed if the agent filters this out.

    # This callback receives the TaskOutput object
    # The actual tool output is in output.raw_output
    raw_tool_output = output.raw_output
    final_answer = output.exported_output

    match = re.search(r"\[RAG_LOG_ID=([^\]]+)\]", raw_tool_output)

    if match:
        log_id = match.group(1)

        with get_engine().connect() as connection:
            query = text("""
                UPDATE rag_evaluation_logs
                SET generated_answer = :generated_answer
                WHERE id = :log_id;
            """)
            connection.execute(query, {
                "generated_answer": final_answer,
                "log_id": log_id
            })
            connection.commit()

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

            retrieved_context = "\n\n".join([f"Source: {row[1]}\nChunk: {row[0]}" for row in results])

            log_query = text("""
                INSERT INTO rag_evaluation_logs (knowledge_card_id, query, retrieved_context)
                VALUES (:kc_id, :query, :retrieved_context)
                RETURNING id;
            """)
            log_result = connection.execute(log_query, {
                "kc_id": self.knowledge_card_id,
                "query": search_query,
                "retrieved_context": retrieved_context
            }).fetchone()
            log_id = log_result[0]

            return f"[RAG_LOG_ID={log_id}]\n\n{retrieved_context}"

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
            agent=self.writer(),
            output_callback=log_rag_output
        )


    @crew
    def create_crew(self) -> Crew:
        # Ensure log directory exists
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(current_dir, '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'log_knowledge.txt')

        """Creates the ContentGenerationCrew"""
        return Crew(
            agents=[self.researcher(), self.writer()],
            tasks=[self.research_task(), self.write_task()],
            verbose=True,
            process=Process.sequential,
            output_log_file=log_file
        )
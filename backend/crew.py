#IOM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
import json
import os
import uuid
from datetime import datetime

from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Azure OpenAI
os.environ["AZURE_API_TYPE"] = "azure"
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_API_VERSION"] = os.getenv("OPENAI_API_VERSION")
os.environ["AZURE_DEPLOYMENT_NAME"] = os.getenv("AZURE_DEPLOYMENT_NAME")
# os.environ["EMBEDDING_MODEL"] = os.getenv("EMBEDDING_MODEL")

# Validate environment variables
required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "OPENAI_API_VERSION", "AZURE_DEPLOYMENT_NAME"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize LLM
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    model=f"azure/{os.getenv('AZURE_DEPLOYMENT_NAME')}",
    # deployment_model=f"azure/{os.getenv('"EMBEDDING_MODEL"')}",
    max_retries=3,
    timeout=30
)

# Load JSON instructions from the config folder
CONFIG_PATH = "config/templates/iom_proposal_template.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    proposal_data = json.load(file)

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
            "combine_example.json"
        ]
    )

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
    #Introducing a new agent- regenerator agent - [NEED TO DISCUSS ON THIS WITH NISHANT]
    @agent
    def regenerator(self) -> Agent:  # ✅ New agent for regeneration
        return Agent(
            config=self.agents_config['regenerator'],
            llm= llm,
            verbose=True
        )
    #Introducing a new agent- regenerator agent - [NEED TO DISCUSS ON THIS WITH NISHANT]

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
    
    #Introducing a new agent- regenerator agent - [NEED TO DISCUSS ON THIS WITH NISHANT]
    # Task: Regenerate content with concise input
    @task
    def regeneration_task(self) -> Task:  # ✅ New task for regeneration
        return Task(
            config=self.tasks_config['regeneration_task']
        )
    #Introducing a new agent- regenerator agent - [NEED TO DISCUSS ON THIS WITH NISHANT]

    @crew
    def generate_proposal_crew(self) -> Crew:  # Ensure method name is correct
        """Creates the ProposalCrew with sequential processing"""
        return Crew(
            agents=[self.content_generator(), self.evaluator()],
            tasks=[self.content_generation_task(), self.evaluation_task()],
            process=Process.sequential,
            verbose=True,
            output_log_file = self.generate_proposal_log,
            knowledge_sources=[self.json_knowledge],           
            embedder={
                "provider": "azure",
                "config": {
                    "model": os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
                    "deployment_id": os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME"),
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                    "api_version": os.getenv("OPENAI_API_VERSION")
                }
            }
        )
       
    #Introducing a new agent- regenerator agent - [NEED TO DISCUSS ON THIS WITH NISHANT]
    @crew
    def regenerate_proposal_crew(self) -> Crew:  # ✅ New crew for regeneration
        """Creates the ProposalCrew for regenerating a section"""
        return Crew(
            agents=[self.regenerator(), self.evaluator()],
            tasks=[self.regeneration_task(), self.evaluation_task()],
            process=Process.sequential,
            verbose=True,
            output_log_file = self.regenerate_proposal_log,
            knowledge_sources=[self.json_knowledge],
            embedder={
                "provider": "azure",
                "config": {
                    "model": os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-ada-002"),
                    "deployment_id": os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"),
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                    "api_version": os.getenv("OPENAI_API_VERSION")
                }
            }
        )
   
    #Introducing a new agent- regenerator agent - [NEED TO DISCUSS ON THIS WITH NISHANT]

    # Move this function to Tools folder
    def generate_final_markdown(self, generated_sections):
        """Compile all generated sections into a markdown file with a unique filename."""

        # ✅ Define a fixed folder name
        folder_name = "proposal-documents"
        folder_path = os.path.join(os.getcwd(), folder_name)

        # ✅ Create the folder if it doesn’t exist
        os.makedirs(folder_path, exist_ok=True)

        # ✅ Generate a unique ID for the file (timestamp + random 6-char UUID)
        unique_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        file_name = f"proposal_document_{unique_id}.md"

        # ✅ Define file path inside the fixed folder
        file_path = os.path.join(folder_path, file_name)

        # ✅ Generate proposal content
        markdown_content = ""
        for section, content in generated_sections.items():
            markdown_content += f"{section}\n{content.strip()}\n\n"

        # ✅ Save the file with a unique name inside the `proposal-documents/` folder
        with open(file_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)

        print(f"✅ Proposal document saved at: {file_path}")



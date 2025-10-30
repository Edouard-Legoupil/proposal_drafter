# backend/utils/crew_legacy_import.py
from crewai import Agent, Task, Crew, Process

class ParameterExtractionCrew:
    def __init__(self, proposal_markdown: str):
        self.proposal_markdown = proposal_markdown

    def run(self):
        # Define Agents
        proposal_analyzer = Agent(
            role='Proposal Analyzer',
            goal='Analyze the provided proposal markdown to identify and extract key parameters like Donor, Main Outcome, Budget Range, and Geographical Scope.',
            backstory='An expert in dissecting project proposals and identifying crucial data points for classification and summary.',
            verbose=True,
            allow_delegation=False
        )

        # Define Tasks
        extraction_task = Task(
            description=f"""
                Analyze the following project proposal markdown and extract the specified parameters.
                Return the results in a JSON format with the following keys: "Targeted Donor", "Main Outcome", "Budget Range", "Geographical Scope", "Country / Location(s)", "Project Draft Short name", "Beneficiaries Profile", "Potential Implementing Partner", "Duration".

                If a parameter cannot be found, the value should be null.

                Proposal Markdown:
                ---
                {self.proposal_markdown}
                ---
            """,
            agent=proposal_analyzer,
            expected_output='A JSON object containing the extracted proposal parameters.'
        )

        # Assemble Crew
        extraction_crew = Crew(
            agents=[proposal_analyzer],
            tasks=[extraction_task],
            process=Process.sequential,
            verbose=True
        )

        # Run the crew
        result = extraction_crew.kickoff()
        return result

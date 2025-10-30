# backend/utils/crew_wizzard.py

from crewai import Agent, Task, Crew

class InsightExtractionCrew:
    def __init__(self):
        pass

    def create_crew(self):
        # Define Agents
        proposal_analyzer = Agent(
            role='Proposal Analyzer',
            goal='Analyze successful project proposals to identify key themes, keywords, and best practices.',
            backstory='An expert in project management and proposal writing, skilled at dissecting documents to uncover the core components of success.',
            verbose=True,
            allow_delegation=False
        )

        insight_synthesizer = Agent(
            role='Insight Synthesizer',
            goal='Synthesize the analyzed proposal data into actionable "do\'s and don\'ts" for future proposal writers.',
            backstory='A seasoned consultant who transforms complex information into clear, concise, and practical advice.',
            verbose=True,
            allow_delegation=False
        )

        # Define Tasks
        analyze_task = Task(
            description='Analyze the provided proposal text to extract key themes, common keywords, and patterns of successful proposals.',
            agent=proposal_analyzer,
            expected_output='A JSON object with three keys: "key_themes", "common_keywords", and "best_practices".'
        )

        synthesize_task = Task(
            description='From the analyzed proposal data, create a list of "do\'s and don\'ts" for writing successful proposals.',
            agent=insight_synthesizer,
            expected_output='A JSON object with one key: "dos_and_donts".'
        )

        # Create Crew
        return Crew(
            agents=[proposal_analyzer, insight_synthesizer],
            tasks=[analyze_task, synthesize_task],
            verbose=2
        )


class WizzardCrew:
    def __init__(self):
        pass

    def create_crew(self):
        # Define Agents
        proposal_analyst = Agent(
            role='Proposal Analyst',
            goal='Analyze the user\'s proposal parameters and prompt against a knowledge base of successful proposals to determine the likelihood of success and identify areas for improvement.',
            backstory='A seasoned grant writer and proposal evaluator with a keen eye for detail and a deep understanding of what makes a proposal successful.',
            verbose=True,
            allow_delegation=False
        )

        strategic_advisor = Agent(
            role='Strategic Advisor',
            goal='Provide a comprehensive analysis and a set of actionable recommendations to improve the proposal, including a revised set of parameters and a more detailed prompt.',
            backstory='A strategic thinker who excels at transforming good ideas into winning proposals.',
            verbose=True,
            allow_delegation=False
        )

        # Define Tasks
        analysis_task = Task(
            description=(
                "Analyze the user's provided proposal parameters and prompt. "
                "Compare them against the provided knowledge base of successful proposals. "
                "Assess the alignment and calculate a 'success_likelihood' score (0.0 to 1.0). "
                "Provide a concise 'analysis_summary' of your findings."
            ),
            agent=proposal_analyst,
            expected_output='A JSON object with two keys: "success_likelihood" and "analysis_summary".'
        )

        recommendation_task = Task(
            description=(
                "Based on the analysis, develop a set of recommendations to improve the proposal. "
                "Suggest a revised set of parameters (donor, outcome, field context, budget). "
                "Also, create a more detailed and compelling 'suggested_prompt' that incorporates the key themes and keywords from the knowledge base."
            ),
            agent=strategic_advisor,
            expected_output='A JSON object with keys for "suggested_donor_id", "suggested_outcome_id", "suggested_field_context_id", "suggested_budget_range", and "suggested_prompt".'
        )

        # Create Crew
        return Crew(
            agents=[proposal_analyst, strategic_advisor],
            tasks=[analysis_task, recommendation_task],
            verbose=2
        )

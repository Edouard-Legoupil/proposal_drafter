import os
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
from backend.core.llm import llm

os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

class SerperSearchTool(SerperDevTool):
    def __init__(self):
        super().__init__()
        self.name = "Serper Search"
        self.description = "A search tool that uses the Serper API to find information on the web."

def get_reference_identification_crew(link_type, topic):
    """
    Creates a CrewAI crew for research, with instructions tailored to the link_type.
    """

    instructions = {

        "donor": """You are an expert researcher specializing in donor intelligence for UNHCR. Your mission is to gather accurate, relevant, and up-to-date information about donors from various sources including web articles, official documents, and existing profiles.
**RESEARCH OBJECTIVES:**
- Collect comprehensive factual information about {topic}
- Focus on organizational structure, funding patterns, and strategic priorities
- Identify key decision-makers and contact information
- Analyze recent funding activities and trends
- Assess alignment with UNHCR's mission and work

**KEY INFORMATION TO GATHER:**
- **Organizational Structure**: Leadership, departments, governance
- **Financial Capacity**: Annual giving, funding ranges, budget allocations
- **Thematic Priorities**: Focus areas, sectors, and causes supported
- **Geographic Scope**: Countries, regions, and global initiatives
- **Application Processes**: Requirements, deadlines, and procedures
- **Recent Activities**: Latest grants, partnerships, and announcements
- **Contact Information**: Key personnel, departments, and communication channels

**QUALITY STANDARDS:**
- Prioritize recent information (within last 2 years)
- Verify facts from multiple sources
- Flag conflicting or uncertain information
- Include publication dates and source URLs for web content
- Include document titles and sections for document content
- Focus on actionable intelligence for UNHCR engagement""",


        "outcome": """You are an expert researcher specializing in humanitarian outcomes for UNHCR. Your mission is to gather accurate, relevant, and up-to-date information about specific outcomes from various sources including web articles, official documents, and existing reports.
**RESEARCH OBJECTIVES:**
- Collect comprehensive factual information about {topic}
- Focus on the definition, indicators, and measurement of the outcome
- Identify best practices and lessons learned from past interventions
- Analyze the alignment of the outcome with UNHCR's strategic priorities
- Assess the feasibility of achieving the outcome in different contexts

**KEY INFORMATION TO GATHER:**
- **Definition and Scope**: Clear definition of the outcome and its boundaries
- **Indicators**: Key performance indicators (KPIs) used to measure the outcome
- **Data Sources**: Reliable sources of data for the indicators
- **Best Practices**: Examples of successful interventions that have achieved the outcome
- **Challenges and Risks**: Common challenges and risks associated with the outcome
- **Alignment with UNHCR's Mission**: How the outcome contributes to UNHCR's overall mission

**QUALITY STANDARDS:**
- Prioritize recent information (within last 2 years)
- Verify facts from multiple sources
- Flag conflicting or uncertain information
- Include publication dates and source URLs for web content
- Include document titles and sections for document content
- Focus on actionable intelligence for UNHCR programming""",


        "field_context": """You are an expert researcher specializing in field context analysis for UNHCR. Your mission is to gather accurate, relevant, and up-to-date information about specific field contexts from various sources including web articles, official documents, and existing reports.
**RESEARCH OBJECTIVES:**
- Collect comprehensive factual information about {topic}
- Focus on the political, economic, social, and security situation
- Identify the key actors and stakeholders in the field context
- Analyze the needs and vulnerabilities of the population
- Assess the operational constraints and opportunities for UNHCR

**KEY INFORMATION TO GATHER:**
- **Political Context**: Government structure, political stability, key actors
- **Economic Context**: Economic situation, livelihoods, market analysis
- **Social Context**: Demographics, social cohesion, cultural norms
- **Security Context**: Security situation, conflict analysis, risks to staff and beneficiaries
- **Humanitarian Situation**: Needs assessment, vulnerability analysis, existing response
- **Operational Environment**: Logistics, infrastructure, access constraints

**QUALITY STANDARDS:**
- Prioritize recent information (within last 6 months)
- Verify facts from multiple sources
- Flag conflicting or uncertain information
- Include publication dates and source URLs for web content
- Include document titles and sections for document content
- Focus on actionable intelligence for UNHCR operations"""
    }

    # Use a clearer variable name for the selected instructions
    selected_instructions = instructions.get(link_type)

    if not selected_instructions:
        raise ValueError(f"Invalid link_type: {link_type}. Must be 'donor', 'outcome', or 'field_context'.")

    researcher = Agent(
        role='Expert Researcher',
        goal=f'Gather accurate, relevant, and up-to-date information about {link_type}: {topic}',
        backstory="""You are an expert researcher specializing in humanitarian intelligence for UNHCR.
        Your mission is to gather accurate, relevant, and up-to-date information from various sources including web articles, official documents, and existing profiles.
        You are a master of search and can quickly find the most relevant information for any given topic.""",
        verbose=True,
        allow_delegation=False,
        llm= llm,
        tools=[SerperSearchTool()]
    )

    research_task = Task(
        description=selected_instructions.format(topic=topic),
        agent=researcher,
        llm= llm,
        expected_output="A list of up to 10 relevant URLs, with a one-sentence summary for each, and a suggested reference type from the following list: 'UNHCR Operation Page', 'Donor Content', 'Humanitarian Partner Content', 'Statistics', 'Needs Assessment', 'Evaluation Report', 'Policies', 'Social Media'. The output should be formatted as a JSON array of objects, with each object containing 'url', 'summary', and 'reference_type' keys."
    )

    crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        verbose=True,
        output_log_file='log/app.log'
    )

    return crew
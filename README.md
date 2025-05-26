
# IOM Project Proposal Generator

An **agentic AI system** powered by [CrewAI](https://docs.crewai.com/introduction) to assist in generating high-quality, structured project proposals tailored for the **International Organization for Migration (IOM)**. This tool is designed to enhance efficiency, consistency, and strategic alignment with IOM’s standards and priorities.

## 🚀 Overview

This system leverages the agent-based framework of **CrewAI** to orchestrate multiple collaborative AI agents—each specialized in a core aspect of proposal writing such as context analysis, objectives formulation, and budgeting.

### Key Features

- 🤖 **Agentic Workflow**: Modular agents simulate a real project development team.
- 🧩 **CrewAI Backbone**: Built using CrewAI for seamless agent collaboration.
- 📝 **Proposal Structuring**: Outputs fully-structured, ready-to-submit project proposals.
- 🌍 **IOM Alignment**: Integrates IOM’s thematic priorities, templates, and compliance requirements.
- 📂 **Contextual Adaptation**: Accepts input on target countries, population groups, and sectors of intervention.

## 🧱 System Architecture

```
+--------------------------+
|     User Input Prompt    |
+--------------------------+
            ↓
+--------------------------+
|      CrewAI Manager      |
+--------------------------+
     ↓        ↓        ↓
+--------+ +--------+ +--------+
| Agent  | | Agent  | | Agent  |  ← e.g., Context Analyst,  etc.
|  1     | |  2     | |  3     |
+--------+ +--------+ +--------+
            ↓
     Final Proposal Draft
```

Each agent is powered by an LLM and follows a role-specific prompt and toolset.

## 🧑‍💼 Example Use Case

**Prompt:**
> Generate a project proposal for enhancing protection and livelihood support for Venezuelan migrants in northern Colombia, with a 12-month duration and a $500,000 USD budget.

**Output:**
A complete proposal document including:
- Executive Summary  
- Background & Needs Assessment  
- Objectives & Outcomes  
- Activities & Work Plan  
- Monitoring & Evaluation  
- Risk Management  
- Budget Overview

## 🛠️ Installation

Refer to CICD-SETUP.md


## 🧪 Status

> 🚧 This project is in active development. Contributions are welcome!

The system uses IOM-standard proposal structures and can be adapted to other UN agencies (e.g., UNHCR, OCHA, UNICEF, WFP).


## 📚 References

- [CrewAI GitHub](https://github.com/joaomdmoura/crewAI)
- [IOM Project Handbook](https://publications.iom.int/system/files/pdf/iom_project_handbook_6feb2012.pdf) 

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Open a pull request

## 📜 License

This project is licensed under the MIT License.

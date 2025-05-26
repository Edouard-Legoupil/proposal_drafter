
# Project Proposal Generator

An open source **agentic AI system** powered by [CrewAI](https://docs.crewai.com/introduction) to assist in generating high-quality, structured project proposals tailored to specific requirement. 

This tool is designed to enhance efficiency, consistency, and strategic alignment with the organisation standards and priorities.

The open source nature of this project allows for community contributions and adaptations, making it a versatile solution for various UN agencies and NGOs.


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

The key configuration files are in `backend/config/agents.yaml` and `backend/config/tasks.yaml`, which define the agents' roles, prompts, and tasks.

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

Refer to [CICD-SETUP.md](https://github.com/iom/proposal_drafter/blob/main/CICD-SETUP.md)


## 🤝 Contributing

> 🚧 This project is licensed under the MIT License. It is in active development. Contributions are welcome!

The system uses IOM-standard proposal structures and can be definitely adapted to other UN Humanitarian agencies (e.g., UNHCR, OCHA, UNICEF, WFP).

If you can contribute to the project, please follow these steps:
1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Open a pull request

## 📚 References

- [CrewAI GitHub](https://github.com/joaomdmoura/crewAI)
- [IOM Project Handbook](https://publications.iom.int/system/files/pdf/iom_project_handbook_6feb2012.pdf) 

Similar (but Proprietary...) Projects

* [grantassistant](https://www.grantassistant.ai/)
* [ai-grant-writing-assistant](https://www.grantable.co/features/ai-grant-writing-assistant)


## 🔮 Future Development: Strategic AI Enhancements

To further elevate the capabilities and value of the IOM Project Proposal Generator, the following future modules are planned, each targeting critical pain points in the project development cycle:

### 1. 🤝 Donor Intelligence Solution

**Pain Point:**  
Project developers often lack timely access to strategic donor information, making it challenging to tailor proposals to specific funding priorities.  

**AI Solution:**  
A dedicated AI agent capable of parsing donor websites, strategic plans, and funding announcements in real-time. It organizes and summarizes insights, generates donor profiles, and suggests alignment strategies for concept notes and proposals. This ensures developers can respond more quickly and strategically to funding opportunities.

**Added Benefits:**  
- Reduces manual effort and time tracking donor priorities  
- Frees up time for creative, strategic work  
- Improves alignment with donor expectations  
- Enhances IOM's strategic positioning, fundraising coherence, and institutional knowledge sharing  
- Supports IOM's branding and communication through accurate, timely engagement materials  

---

### 2. 📊 Results-Matrix Generator

**Pain Point:**  
Many staff find it challenging to develop SMART indicators and logically linked results frameworks, especially under tight deadlines. Knowledge is fragmented, and lessons from past projects are not easily accessible.

**AI Solution:**  
A results-matrix generator that translates narrative goals and problem statements into structured results chains. It suggests indicators, verification sources, and assumptions based on context and thematic focus, enhancing clarity and alignment.

**Added Benefits:**  
- Streamlines complex framework design  
- Improves quality and consistency of M&E planning  
- Enables knowledge transfer through reusable logic models  
- Strengthens institutional M&E standards and reporting quality  

---

### 3. 🔁 Project Cycle Integration Engine

**Pain Point:**  
Lessons learned and institutional knowledge are poorly consolidated and often inaccessible during project design. Staff turnover and siloed feedback processes lead to repeated mistakes and inconsistent quality.

**AI Solution:**  
An AI-driven engine to extract and synthesize learnings from evaluation reports, monitoring data, and past project documentation. It surfaces relevant examples and best practices directly into the proposal development workflow.

**Added Benefits:**  
- Ensures access to real-world lessons and strategies  
- Encourages evidence-based innovation  
- Reduces redundancy and promotes adaptive programming  
- Strengthens project effectiveness and organizational memory  

---

These future developments aim to transform the IOM Proposal Generator into a comprehensive **AI-powered Project Development Suite**, aligning creativity with institutional wisdom and real-time intelligence to drive measurable impact.

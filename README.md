
# Project Proposal Generator

__Empowering change-makers with AI-enhanced Proposal Drafting__


## Introduction

The Project Proposal Generator is an open-source, agentic AI system, designed to automate and enhance the creation of high-quality, structured project proposals. Tailored for UN agencies, NGOs, and mission-driven organizations, it ensures strategic alignment, compliance, and efficiency—turning complex requirements into compelling, submission-ready drafts.

### ✨ Why This Tool?

- __AI-Powered Collaboration__: Simulates a real proposal team with specialized agents handling research, budgeting, and drafting.

- __Strategic Precision__: Aligns proposals with organizational priorities, findings from previous evaluations, donor guidelines, and thematic frameworks.

- __Adaptable & Open-Source__: Customizable for diverse sectors and editable by the community.

- __Seamless Export__: Generate, refine, and export proposals in Word/PDF with validation tracking.

#### 🌍 Impact

By streamlining proposal development, this tool accelerates funding opportunities, reduces manual effort, and ensures consistency—helping changemakers focus on impact, not paperwork.

### Key Features:

- 🤖 **Agentic Workflow**: Modular agents simulate a real project development team.
- 📝 **Proposal Structuring**: Outputs fully-structured, ready-to-submit project proposals.
- 🌍 **Alignment**: Integrates thematic priorities, templates, and compliance requirements.
- 🧩 **Contextual Adaptation**: Accepts input on target countries, population groups, and sectors of intervention.
- 📂 **Validation & Export**: Projects can be edit and refined, then exported to word and pdf and marked as validated.

The open source nature of this project allows for community contributions and adaptations, making it a versatile solution for various UN agencies and NGOs.

## 🚀 Overview

This system leverages the agent-based framework of ** [CrewAI](https://docs.crewai.com/introduction) ** to orchestrate multiple collaborative AI agents—each specialized in a core aspect of proposal writing such as context analysis, objectives formulation, and budgeting.


## 🧱 System Architecture


Each agent is powered by an LLM and follows a role-specific prompt and toolset.

The key configuration files are in `backend/config/agents.yaml` and `backend/config/tasks.yaml`, which define the agents' roles, prompts, and tasks.

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


## 🔮 Future Development: Strategic AI Enhancements

To further elevate the capabilities and value of the this Project Proposal Generator, the following future modules are planned, each targeting critical pain points in the project development cycle. These future developments aim to transform this initial Proposal Generator into a comprehensive **AI-powered Project Development Suite**, aligning creativity with institutional wisdom and real-time intelligence to drive measurable impact.

### 1. 🤝 Donor Intelligence Solution

**Pain Point:**  
Project developers often lack timely access to strategic donor information, making it challenging to tailor proposals to specific funding priorities.  

**Solution:**  
A dedicated tools capable of parsing donor websites, strategic plans, and funding announcements in real-time. It should organize and summarize insights, generate donor profiles, and suggest alignment strategies for concept notes and proposals. This ensures developers can respond more quickly and strategically to funding opportunities.

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

**Solution:**  
A results-matrix generator that translates narrative goals and problem statements into structured results chains. It suggests indicators, verification sources, and assumptions based on context and thematic focus, enhancing clarity and alignment.

**Added Benefits:**  
- Streamlines complex framework design  
- Improves quality and consistency of M&E planning  
- Enables knowledge transfer through reusable logic models  
- Strengthens institutional M&E standards and reporting quality  

---

### 3. 📚 Knowledge Injection from Evaluation Recommendations

**Pain Point:**  
Lessons learned from evaluations are not consistently integrated into new proposals. These insights are scattered across reports and often overlooked due to time constraints, limited access, or lack of awareness.

**Solution:**  
An intelligent extraction engine that analyzes and summarizes key findings, recommendations, and good practices from evaluation and monitoring reports. It embeds these insights contextually into the proposal writing process.

**Added Benefits:**  
- Ensures use of real-world learning to improve design  
- Reduces repeated mistakes by surfacing relevant recommendations  
- Strengthens adaptive management and institutional memory  
- Enhances proposal credibility and quality with evidence-backed design

---

### 4. 💰 AI-Powered Budget Builder with Calibrated Costing Tool

**Pain Point:**  
Developing budgets that align with real costs and institutional norms is time-consuming and error-prone. There is often inconsistency in pricing across proposals and a lack of reference to standard costing.

**Solution:**  
An AI agent that generates budget lines using a calibrated costing tool referencing standard rates and historical financial data, in a similar approach than [IRC SCAN](https://www.rescue.org/sites/default/files/document/964/ircscantool2pager.pdf). The system ensures consistency, transparency, and realism in project budgeting.

**Added Benefits:**  
- Saves time and increases accuracy in budget development  
- Promotes financial coherence across projects and missions  
- Builds donor confidence through realistic and traceable costing  
- Facilitates rapid budget iteration for concept notes and revisions  

---

### 5. ✅ Project Development Validation Workflow

**Pain Point:**  
Project proposals often move through inconsistent or unclear validation processes. Responsibilities and checkpoints vary across missions, leading to delays, miscommunication, or insufficient quality control.

**Solution:**  
A structured validation workflow supported by AI agents that route proposals through pre-defined quality assurance steps. These may include thematic peer review, budgeting checks, risk scanning, and senior management approval.

**Added Benefits:**  
- Increases clarity and accountability in project design  
- Strengthens institutional quality standards  
- Reduces rework and improves time to submission  
- Builds team collaboration and internal buy-in  

---

### 6. 📝 AI-Supported Reporting & Documentation Toolkit

**Pain Point:**  
Project teams often struggle with reporting due to inconsistent formats, fragmented data sources, and unclear requirements. Generating accurate, timely, and donor-compliant reports can be burdensome, especially when field data is lacking or not well-structured.

**Solution:**  
An integrated module that provides tailored reporting templates aligned with donor and institutional requirements. It includes data collection form generators and AI assistants that help extract, summarize, and format content for interim and final reports.

**Added Benefits:**  
- Standardizes and simplifies reporting practices across projects  
- Reduces staff burden with ready-to-use templates and content suggestions  
- Increases quality, timeliness, and compliance of submitted reports  
- Supports continuous learning by linking reported outcomes to future project design  
- Facilitates better data collection through context-aware form generation


--------

## 📚 References

This project was impulsed by [Edouard Legoupil, IOM chief Data Officer](https://www.linkedin.com/in/edouardlegoupil/recent-activity/all/) and jointly developped with [Datamatics](). It is building on the [IOM Project Handbook](https://publications.iom.int/system/files/pdf/iom_project_handbook_6feb2012.pdf) 

Similar (but Proprietary...) Projects

* [grantassistant](https://www.grantassistant.ai/)
* [ai-grant-writing-assistant](https://www.grantable.co/features/ai-grant-writing-assistant)


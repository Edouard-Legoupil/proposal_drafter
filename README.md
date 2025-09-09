
# Project Proposal Generator

__Empowering change-makers with AI-enhanced Proposal Drafting__


## Introduction

The Project Proposal Generator is an open-source, agentic AI system, designed to automate and enhance the creation of high-quality, structured project proposals. Tailored for UN agencies, NGOs, and mission-driven organizations, it ensures strategic alignment, compliance, and efficiency—turning complex requirements into compelling, submission-ready drafts.

### ✨ Why This Tool?

By streamlining proposal development, this tool accelerates funding opportunities, reduces manual effort, and ensures consistency—helping changemakers focus on impact, not paperwork.

- __AI-Powered Collaboration__: Simulates a real proposal team with specialized agents handling research, budgeting, and drafting.

- __Strategic Precision__: Aligns proposals with organizational priorities, findings from previous evaluations, donor guidelines, and thematic frameworks.

- __Adaptable & Open-Source__: Customizable for diverse sectors and editable by the community.

- __Seamless Export__: Generate, refine, and export proposals in Word/Excel with validation tracking.


## 🚀 Overview

The landing page is the first thing you'll see. From here, you can navigate to all the key features.

![Landing Page](playwright/test-results/1_landing.png)

## 2. User Registration

To get started, you'll need to register for an account. Click on the "Register" button on the landing page to go to the registration form.

Fill in your details in the __registration form__ as shown below.

![Registration Page Before Submit](playwright/test-results/2_register_page_before_submit.png)

Once you've filled in all the required fields, click the "Submit" button. You should see a confirmation that your registration was successful.

![Registration Page After Submit](playwright/test-results/3_register_page_after_submit.png)

Once you are logged in, you can __generate a new proposal__. Navigate to the "Generate Proposal" page.

![Generate Proposal](playwright/test-results/4_generate_proposal.png)

After you have filled out the necessary information, click "Generate". You will see a confirmation that your proposal has been created.

![Proposal Created](playwright/test-results/5_proposal_created.png)


After a proposal is created, it can be sent for __peer review__. The peer review page allows you to view the proposal and provide feedback.

![Peer Review](playwright/test-results/6_peer_review.png)

__Knowledge cards__ are a way to represent information in a concise and easy-to-digest format.

![Knowledge Card](playwright/test-results/9_knowledge_card.png)

You can create new knowledge cards from the "Create Knowledge Card" page.

![Create Knowledge Card](playwright/test-results/10_knowledge_card_create.png)


### 🌍 Key Features:

This system leverages the agent-based framework of [CrewAI](https://docs.crewai.com/introduction) to orchestrate multiple collaborative AI agents—each specialized in a core aspect of proposal writing such as context analysis, objectives formulation, and budgeting.

- 🤖 **Agentic Workflow**: Modular agents simulate a real project development team.
- 📝 **Proposal Structuring**: Outputs fully-structured, ready-to-submit project proposals.
- 🌍 **Alignment**: Integrates thematic priorities, templates, and compliance requirements.
- 🧩 **Contextual Adaptation**: Accepts input on target countries, population groups, and sectors of intervention.
- 📂 **Validation & Export**: Projects can be edit and refined, then exported to word and pdf and marked as validated.





## 🧱 System Architecture


Each agent is powered by an LLM and follows a role-specific prompt and toolset.

The key configuration files are in `backend/config/agents.yaml` and `backend/config/tasks.yaml`, which define the agents' roles, prompts, and tasks.
 
![AI Agent Crew Description](https://raw.githubusercontent.com/iom/proposal_drafter/refs/heads/main/img/crew.png) 



## 🛠️ Installation

Refer to [doc_running_local.md](https://github.com/iom/proposal_drafter/blob/main/doc_running_local.md)

## 🔒 Security

This project prioritizes security to ensure the safe handling of sensitive information and the integrity of the proposal generation process. Our approach to security includes the following considerations:

*   **Data Privacy**: As the application is designed to work from Public Data Sources, elements related to Data Protection in relation Personally Identifiable Information do not apply.
*   **Secure Coding Practices**: We adhere to secure coding standards to minimize vulnerabilities. This includes practices like input validation to prevent common security flaws. A large part of the codebase has been created through [vibe coding](https://en.wikipedia.org/wiki/Vibe_coding) interactions with [Google Jules](https://jules.google.com) 
*   **Dependency Management**: We actively manage our open-source dependencies and use tools to scan for known vulnerabilities. We strive to keep all libraries up-to-date to protect against security threats.
*   **LLM Security**: For the AI components, we are mindful of risks such as prompt injection. We design our prompts and agentic workflows to be robust against malicious inputs and to ensure the Large Language Model (LLM) behaves within its intended scope.


## 🤝 Contributing

> 🚧 This project is licensed under the MIT License. It is in active development. Contributions are welcome!

The system uses IOM-standard proposal structures and can be definitely adapted to other UN Humanitarian agencies (e.g., UNHCR, OCHA, UNICEF, WFP).

If you can contribute to the project, please follow these steps:
1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Open a pull request


## 🌐 Alignment with UN Open Source Principles

The open source nature of this project allows for community contributions and adaptations, making it a versatile solution for various UN agencies and NGOs.

This project is committed to upholding the [UN Open Source Principles](https://unite.un.org/en/news/osi-first-endorse-united-nations-open-source-principles), ensuring it is a transparent, collaborative, and sustainable solution for the humanitarian community.

-   **Open by Default**: The Project Proposal Generator is built as an open-source tool from the ground up, making its codebase and development process accessible to everyone.
-   **Contribute Back**: We actively encourage and welcome contributions from the community to foster a vibrant ecosystem of developers and users.
-   **Secure by Design**: Security is a core consideration in our development lifecycle, ensuring that the tool is safe and reliable for all users.
-   **Foster Inclusive Participation**: We are dedicated to creating an inclusive environment where individuals from diverse backgrounds can contribute and feel empowered.
-   **Design for Reusability**: The modular architecture of the system allows for easy adaptation and integration with other platforms and ecosystems.
-   **Provide Documentation**: Comprehensive documentation is provided for end-users, integrators, and developers to ensure clarity and ease of use.
-   **RISE (Recognize, Incentivize, Support, and Empower)**: We aim to empower our community by recognizing contributions and providing the necessary support for active participation.
-   **Sustain and Scale**: The project is designed to be a long-term solution that can evolve and scale to meet the changing needs of the UN system and its partners.


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

* [grantassistant](https://www.grantassistant.ai)
* [ai-grant-writing-assistant](https://www.grantable.co)
* [bidnexus](https://www.bidnexus.ai)


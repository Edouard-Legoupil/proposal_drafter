# Proposal Template Format

The JSON proposal templates are used in the AI Project Proposal Generator. These templates provide a flexible way to define the structure, content, and generation instructions for various types of proposals.

 Those files are used to generate proposals for different donors and proposal types through the backend/utils/crew_proposal.py and backend/api/proposal.py  file: generate_all_sections_background function.

All proposal templates are stored in the `backend/templates` directory and follow the naming convention `template_type_donor.json`.

## Top-Level Structure

Each proposal template is a JSON object with the following top-level properties:

-   `template_type`: (String) The type of the template (e.g., "Proposal").
-   `donors`: (Array of Strings) A list of donor names that this template applies to.
-   `special_requirements`: (Object) *Optional.* Defines global instructions that apply to the generation of *every* section in the proposal.
    -   `instructions`: (Array of Strings) A list of high-level requirements (e.g., tone of voice, forbidden phrases, strategic emphasis).
-   `sections`: (Array of Objects) The main part of the template, defining each section of the proposal. Each object in this array represents a section.

## Section Properties

Each object within the `sections` array defines a single section of the proposal and can have the following properties:

| Property           | Type          | Description                                                                                                                                                                  |
| ------------------ | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `section_name`     | String        | **Required.** The unique internal identifier for the section.                                                                                                                |
| `section_label`    | String        | *Optional.* The display name for the section when exported to a Word document. If omitted, `section_name` is used.                                                             |
| `section_parent`   | String        | *Optional.* If provided, sections with the same `section_parent` value will be grouped under a common Level 1 heading in the Word export. The `section_label` will be a Level 2 heading. |
| `format_type`      | String        | **Required.** Determines the type of content to be generated for the section. See [Format Type Details](#format-type-details) for more information.                            |
| `instructions`     | String        | **Required** (for AI formats). Provides guidance to the AI on how to generate the content for the section.                                                                                      |
| `mandatory`        | Boolean       | **Required.** Indicates whether the section is mandatory. Default should be considered `true`.                                                                                                     |
| `word_limit`       | Number        | *Optional.* A suggested word limit for the generated text (applicable primarily to `text` format).                                                                           |
| `...`              | `any`         | Additional properties may be required depending on the chosen `format_type`.                                                                                                 |



---

## instructions

This is a key property for the AI to understand what is expected in the section. It should be clear and concise and implement best practices for AI instructions to prevent ambiguity.

----
## Format Type Details

The `format_type` property is crucial as it dictates how the content for a section is generated and what additional properties are needed.

### 1. `text`

Generates a free-form text paragraph.

-   **`word_limit`**: (Number) *Optional.* A suggested word limit for the generated text.

**Example:**

```json
{
  "section_name": "Summary",
  "section_label": "1.6. Project Summary",
  "section_parent": "1. Overview",
  "format_type": "text",
  "mandatory": true,
  "word_limit": 300,
  "instructions": "Write a comprehensive project summary covering: 1) Context (crisis overview), 2) Key objectives (max 3), 3) Expected impact (quantifiable where possible), 4) Main activities (bullet points)."
}
```

### 2. `fixed_text`

Inserts a predefined, static string of text into the section. The AI is not used for this format type.

-   **`fixed_text`**: (String) **Required.** The exact text to be inserted into the document.

**Example:**

```json
{
  "section_name": "Introduction",
  "section_label": "1. Introduction",
  "section_parent": "1. Overview",
  "format_type": "fixed_text",
  "mandatory": true,
  "fixed_text": "This is a fixed text introduction that will appear in every proposal using this template."
}
```

### 3. `number`

Generates a response that should strictly be a number.

-   The `instructions` should clearly ask for a numerical value.

**Example:**

```json
{
  "section_name": "Funds Required for Organization Response",
  "section_label": "2.1. Total Funds Required for Organization Response",
  "section_parent": "2. Funding summary and Country Context",
  "format_type": "number",
  "mandatory": true,
  "instructions": "Calculate and present the total funding requirements by referencing HRP/flash appeal figures if available."
}
```

### 4. `table`

Generates content in a Markdown table format based on a defined structure.

-   **`columns`**: (Array of Objects) **Required.** Defines the header and format for each column in the table. Each object in the array should have:
    -   `name`: (String) The column header text.
    -   `format_type`: (String) The expected format of the cells in this column (e.g., `text` or `number`).
    -   `instructions`: (String) Instructions for how to fill out the cells in this column.
-   **`rows`**: (Array of Objects) *Optional.* Defines the structure and instructional content for each row (if rows are static). Each object in the array should have:
    -   `row_title`: (String) The title of the row (e.g., "Outcome 1").
    -   `instructions`: (String) Instructions for how to fill out this row.

**Example:**

```json
{
  "section_name": "Logical Framework",
  "section_label": "5. Logical Framework by Sector",
  "format_type": "table",
  "mandatory": true,
  "instructions": "Develop a results framework with outcomes, outputs, and SMART indicators.",
  "columns": [
    {
      "name": "Indicator",
      "format_type": "text",
      "instructions": "Quantitative or qualitative factors to measure achievement."
    },
    {
      "name": "Target (Men/Women/Boys/Girls)",
      "format_type": "number",
      "instructions": "Provide a target number for each group: XX/XX/XX/XX"
    },
    {
      "name": "Means of Verification",
      "format_type": "text",
      "instructions": "How will the indicator be measured? Example: Partner reports, UNHCR reports, post-distribution monitoring"
    }
  ],
  "rows": [
    {
      "row_title": "Outcome 1",
      "instructions": "The intended changes in institutional performance or group behaviour."
    },
    {
      "row_title": "Output 1.1",
      "instructions": "The intended changes in the skills or abilities of the beneficiaries."
    }
  ]
}
```




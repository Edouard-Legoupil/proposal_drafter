# Backend Scripts

This directory contains utility scripts for managing the backend of the Proposal Generator application. All scripts are equipped with a logging system that outputs to both the console and a corresponding log file in the `log/` directory, ensuring that all operations are recorded and can be easily debugged.

## `1-populate_knowledge_cards.py`

This script populates the database with initial data from a multi-sheet Excel file. It seeds the `donors`, `outcomes`, and `field_contexts` tables, creates a default knowledge card for each entry, and links them to associated references.

### Prerequisites

1.  **Excel File**: The script requires an Excel file with four worksheets: `field_contexts`, `donor`, `outcome`, and `reference`. A template file, `seed_data.xlsx`, is provided in the `db/` directory.

2.  **User ID**: You must provide the UUID of an existing user in the database. The created records will be associated with this user.

3.  **Dependencies**: activate the app virtual environment 

```bash
source backend/venv/bin/activate
```


### How to Get a `user_id`

You can get a `user_id` by connecting to the database with `psql` and running the following command:

```bash
psql -h localhost -U <your_username> -d <your_database_name> -c "SELECT id FROM users LIMIT 1;"
```

### Usage

Run the script from the root directory of the project, providing the `user_id`. The script will use the default Excel file path (`db/seed_data.xlsx`).

```bash
python3 backend/scripts/1-populate_knowledge_cards.py --user-id <your_user_id>
```

You can also specify a different path to the Excel file using the `--excel-file` argument:

```bash
python3 backend/scripts/populate_knowledge_cards.py --excel-file /path/to/your/data.xlsx --user-id <your_user_id>
```


## `2-update_embeddings.py`

This script updates the vector embeddings for all references stored in the `knowledge_card_references` table. It can be used to generate embeddings for new references or to refresh existing ones.

### How It Works

By default, the script will:
1.  Fetch all references from the database.
2.  For each reference, it will try to reconstruct the original text content from the `knowledge_card_reference_vectors` table.
3.  If no existing text chunks are found, it will scrape the content from the reference's URL.
4.  It will then re-generate the embeddings for the content and store them in the database.

### Usage

To run the script, execute the following command from the root directory of the project:

```bash
python3 backend/scripts/2-update_embeddings.py
```

### Forcing Re-scraping

If you want to force the script to re-scrape the content from all reference URLs, even if they have already been processed, use the `--force-rescrape` flag:

```bash
python3 backend/scripts/2-update_embeddings.py --force-rescrape
```



## `3-generate_card_content.py`

This script automatically generates content for knowledge cards that are either missing content or have outdated information based on the `updated_at` timestamp of their references.

### How It Works

1.  **Identifies Cards for Generation**: The script determines which knowledge cards need content generation. This includes:
    *   Cards with no existing generated sections.
    *   Cards where a linked reference has been updated more recently than the card itself.
    *   All cards, if the `--force` flag is used.

2.  **Generates Content**: For each identified card, it uses the `ContentGenerationCrew` to generate content for all sections defined in the card's template.

3.  **Saves to Database and File**: The newly generated content is saved to the `generated_sections` column in the `knowledge_cards` table. Additionally, the content is saved to a JSON file in the `backend/knowledge/` directory, ensuring consistency with the API's behavior.

4.  **Creates History Entry**: A new entry is created in the `knowledge_card_history` table to snapshot the changes.

### Usage

To run the script, you must provide the UUID of an existing user to associate with the history entries.

```bash
python3 backend/scripts/3-generate_card_content.py --user-id <your_user_id>
```

To force the regeneration of content for all knowledge cards, regardless of their current state, use the `--force` flag:

```bash
python3 backend/scripts/3-generate_card_content.py --force --user-id <your_user_id>
```

## `4-find-references.py`

This script automates the discovery and linking of web references for existing knowledge cards. It uses an AI agent (`ReferenceIdentificationCrew`) to search for relevant URLs based on the name/topic of each knowledge card and populates the `knowledge_card_references` table.

### How It Works

1.  **Selects Target Cards**: Based on the `card_type` argument (`outcome`, `field_context`, `donor`, or `all`), it retrieves the ID and name of relevant cards from the database.
2.  **AI Reference Search**: For each card, it triggers the `ReferenceIdentificationCrew` to find relevant web resources.
3.  **Extracts URLs**: It parses the AI agent's output to extract URLs.
4.  **Updates Database**:
    *   Checks if the URL already exists in `knowledge_card_references`.
    *   If not, creates a new reference entry.
    *   Links the reference to the specific knowledge card in the `knowledge_card_to_references` table.

### Usage

The script requires a `--card-type` (or `all`) and a valid `--user-id` for auditing purposes.

To find references for **all** knowledge card types:

```bash
python3 backend/scripts/4-find-references.py --card-type all --user-id <your_user_id>
```

To find references for a **specific** type (e.g., `donor`):

```bash
python3 backend/scripts/4-find-references.py --card-type donor --user-id <your_user_id>
```

**Available Card Types:**
*   `outcome`
*   `field_context`
*   `donor`
*   `all`


# Validate All Templates

A comprehensive validation script that ensures all proposal and concept note templates are correctly configured and consistent.

```bash
python3 backend/scripts/validate_templates.py
```
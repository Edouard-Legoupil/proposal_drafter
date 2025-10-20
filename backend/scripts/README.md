# Backend Scripts

This directory contains utility scripts for managing the backend of the Proposal Generator application.

## `populate_knowledge_cards.py`

This script populates the database with initial data for donors, outcomes, and field contexts, creating a default knowledge card and associated references for each entry.

### Prerequisites

1.  **CSV Files**: The script requires three CSV files with specific columns. Examples are provided in the `db/` directory:
    *   `donors_references.csv`: `name,account_id,country,donor_group,url,reference_type,summary`
    *   `outcomes_references.csv`: `name,url,reference_type,summary`
    *   `field_contexts_references.csv`: `name,title,category,geographic_coverage,url,reference_type,summary`

2.  **User ID**: You must provide the UUID of an existing user in the database. The created records will be associated with this user.

### How to Get a `user_id`

You can get a `user_id` by connecting to the database with `psql` and running the following command:

```bash
psql -h localhost -U <your_username> -d <your_database_name> -c "SELECT id FROM users LIMIT 1;"
```

### Usage

Run the script from the root directory of the project, providing the paths to the three CSV files and the `user_id`.

```bash
python3 backend/scripts/populate_knowledge_cards.py \
  --donors-file db/donors_references.csv \
  --outcomes-file db/outcomes_references.csv \
  --field-contexts-file db/field_contexts_references.csv \
  --user-id <your_user_id>
```

## `update_embeddings.py`

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
python3 backend/scripts/update_embeddings.py
```

### Forcing Re-scraping

If you want to force the script to re-scrape the content from all reference URLs, even if they have already been processed, use the `--force-rescrape` flag:

```bash
python3 backend/scripts/update_embeddings.py --force-rescrape
```
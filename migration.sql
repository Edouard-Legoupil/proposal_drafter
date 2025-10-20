-- Migration script to change the one-to-many relationship between knowledge_cards and
-- knowledge_card_references to a many-to-many relationship.

BEGIN;

-- Step 1: Create a temporary table to hold the unique references.
-- We select the first occurrence of each URL as the master reference.
CREATE TABLE knowledge_card_references_unique AS
SELECT DISTINCT ON (url)
    id,
    url,
    reference_type,
    summary,
    created_by,
    created_at,
    updated_by,
    updated_at,
    scraped_at,
    scraping_error
FROM knowledge_card_references;

-- Step 2: Create the new join table for the many-to-many relationship.
CREATE TABLE knowledge_card_to_references (
    knowledge_card_id UUID NOT NULL,
    reference_id UUID NOT NULL,
    PRIMARY KEY (knowledge_card_id, reference_id)
);

-- Step 3: Populate the new join table by mapping old references to the new unique references.
INSERT INTO knowledge_card_to_references (knowledge_card_id, reference_id)
SELECT
    kcr.knowledge_card_id,
    kcru.id
FROM
    knowledge_card_references kcr
JOIN
    knowledge_card_references_unique kcru ON kcr.url = kcru.url
ON CONFLICT (knowledge_card_id, reference_id) DO NOTHING;

-- Step 4: Update the foreign keys in the vectors table.
-- We need a mapping from the old reference IDs to the new unique reference IDs.
UPDATE knowledge_card_reference_vectors kcrv
SET reference_id = kcru.id
FROM
    knowledge_card_references kcr
JOIN
    knowledge_card_references_unique kcru ON kcr.url = kcru.url
WHERE
    kcrv.reference_id = kcr.id;

-- Step 5: Drop the old references table and rename the new one.
-- The vectors table has a dependency. Let's drop and re-add it.
ALTER TABLE knowledge_card_reference_vectors DROP CONSTRAINT IF EXISTS knowledge_card_reference_vectors_reference_id_fkey;

DROP TABLE knowledge_card_references;

ALTER TABLE knowledge_card_references_unique RENAME TO knowledge_card_references;

-- Step 6: Re-establish primary key and constraints on the new references table.
ALTER TABLE knowledge_card_references ADD PRIMARY KEY (id);
ALTER TABLE knowledge_card_references ADD CONSTRAINT knowledge_card_references_url_key UNIQUE (url);

-- Step 7: Re-add the foreign key constraints.
ALTER TABLE knowledge_card_reference_vectors
ADD CONSTRAINT knowledge_card_reference_vectors_reference_id_fkey
FOREIGN KEY (reference_id) REFERENCES knowledge_card_references(id) ON DELETE CASCADE;

ALTER TABLE knowledge_card_to_references
ADD CONSTRAINT fk_knowledge_card
FOREIGN KEY (knowledge_card_id) REFERENCES knowledge_cards(id) ON DELETE CASCADE;

ALTER TABLE knowledge_card_to_references
ADD CONSTRAINT fk_reference
FOREIGN KEY (reference_id) REFERENCES knowledge_card_references(id) ON DELETE CASCADE;

-- Step 8: Update indices if they were dropped or need to be recreated.
DROP INDEX IF EXISTS idx_knowledge_card_references_knowledge_card_id;
DROP INDEX IF EXISTS idx_knowledge_card_references_knowledge_card_id;
CREATE INDEX IF NOT EXISTS idx_knowledge_card_to_references_knowledge_card_id ON knowledge_card_to_references(knowledge_card_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_card_to_references_reference_id ON knowledge_card_to_references(reference_id);

COMMIT;
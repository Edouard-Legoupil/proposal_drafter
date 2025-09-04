-- Clear existing data
TRUNCATE TABLE teams, users, donors, outcomes, field_contexts, proposals, proposal_donors, proposal_outcomes, proposal_field_contexts, proposal_peer_reviews, proposal_status_history, knowledge_cards, knowledge_card_references RESTART IDENTITY CASCADE;

-- Insert Teams with properly formatted UUIDs
INSERT INTO teams (id, name) VALUES
('11111111-1111-4111-8111-111111111111', 'DRRM'),
('22222222-2222-4222-8222-222222222222', 'HQ Protection'),
('33333333-3333-4333-8333-333333333333', 'Test');

-- Insert Users with consistent UUIDs
INSERT INTO users (id, email, password, name, team_id) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'user1@example.com', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Alice', '11111111-1111-4111-8111-111111111111'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', 'user2@example.com', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Bob', '11111111-1111-4111-8111-111111111111'),
('cccccccc-cccc-4ccc-8ccc-cccccccccccc', 'user3@example.com', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Charlie', '22222222-2222-4222-8222-222222222222');

-- Insert Outcomes with pre-defined UUIDs for consistency
INSERT INTO outcomes (id, name) VALUES
('44444444-4444-4444-8444-444444444444', 'OA1-Access/Documentation');

-- Insert Donors with pre-defined UUIDs
INSERT INTO donors (id, name, country, donor_group) VALUES
('00000000-0000-4000-8000-000000000011', 'United States of America - Population Refugee & Migration', 'USA', 'DRRM Donor Group 3');

-- Insert Field Contexts with pre-defined UUIDs
INSERT INTO field_contexts (id, title, name, category, geographic_coverage) VALUES
('00000000-0000-4000-8000-000000000112', 'Colombia Situation', 'Colombia', 'Country', 'One Country Operation');

-- Link proposals (using the same pattern for UUID consistency)
DO $$
DECLARE
    proposal1_id uuid := '00000000-0000-4000-8000-000000000201';
    proposal2_id uuid := '00000000-0000-4000-8000-000000000202';
    proposal3_id uuid := '00000000-0000-4000-8000-000000000203';
    alice_id uuid := 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
    bob_id uuid := 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
    donor1_id uuid := '00000000-0000-4000-8000-000000000011';
    outcome1_id uuid := '44444444-4444-4444-8444-444444444444';
    context1_id uuid := '00000000-0000-4000-8000-000000000112';
BEGIN
    -- Insert Proposal 1 (for pre-submission review)
    INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
    (proposal1_id, alice_id, 'unhcr_proposal_template.json', '{"Project Draft Short name": "Colombia Shelter Project", "Budget Range": "500k$"}', 'A project to provide shelter for displaced persons in Colombia.', 'submission', NOW() - INTERVAL '10 days', NOW() - INTERVAL '5 days');
    INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (proposal1_id, donor1_id);
    INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (proposal1_id, outcome1_id);
    INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (proposal1_id, context1_id);
    INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, status, section_name, review_text) VALUES (proposal1_id, bob_id, 'completed', 'Executive Summary', 'This section needs more detail on the target population.');

    -- Insert Proposal 2 (approved)
    INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
    (proposal2_id, alice_id, 'unhcr_proposal_template.json', '{"Project Draft Short name": "Child Protection Ukraine", "Budget Range": "1M$"}', 'A project for child protection in Ukraine.', 'approved', NOW() - INTERVAL '30 days', NOW() - INTERVAL '2 days');

    -- Insert Knowledge Card
    INSERT INTO knowledge_cards (id, title, summary, donor_id) VALUES
    ('11111111-1111-1111-1111-111111111111', 'USAID Funding Priorities', 'A summary of USAID funding priorities.', donor1_id);
END $$;

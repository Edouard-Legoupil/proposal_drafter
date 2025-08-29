-- Clear existing data
TRUNCATE TABLE users, donors, outcomes, field_contexts, proposals, proposal_donors, proposal_outcomes, proposal_field_contexts, proposal_peer_reviews, proposal_status_history, knowledge_cards, knowledge_card_references RESTART IDENTITY CASCADE;

-- Insert Users
-- Passwords are all 'password123'
INSERT INTO users (id, email, password, name, team) VALUES
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'user1@example.com', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Alice', 'Team Alpha'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'user2@example.com', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Bob', 'Team Alpha'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'user3@example.com', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Charlie', 'Team Bravo');

-- Insert Donors
INSERT INTO donors (id, account_id, name, country, donor_group) VALUES
('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'USAID123', 'USAID', 'USA', 'Government'),
('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'ECHO456', 'ECHO', 'EU', 'IGO'),
('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'SIDA789', 'SIDA', 'Sweden', 'Government');

-- Insert Outcomes
INSERT INTO outcomes (id, name) VALUES
('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OA1-Access/Documentation'),
('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'OA5-Child protection'),
('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'OA9-Housing');

-- Insert Field Contexts
INSERT INTO field_contexts (id, title, name, category, geographic_coverage) VALUES
('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Colombia Situation', 'Colombia', 'Country', 'One Country Operation'),
('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Venezuela Situation', 'Venezuela', 'Country', 'One Country Operation'),
('f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'East Africa Route', 'East Africa', 'Region', 'Route-Based-Approach');

-- Insert Proposals
-- Proposal 1 (by Alice, Team Alpha)
INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'unhcr_proposal_template.json', '{"Project Draft Short name": "Colombia Shelter Project", "Budget Range": "500k$"}', 'A project to provide shelter for displaced persons in Colombia.', 'in_review', NOW() - INTERVAL '10 days', NOW() - INTERVAL '5 days');

INSERT INTO proposal_donors (proposal_id, donor_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13');
INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, status) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'pending');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'draft', NOW() - INTERVAL '10 days');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'in_review', NOW() - INTERVAL '5 days');

-- Proposal 2 (by Bob, Team Alpha)
INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'unhcr_proposal_template.json', '{"Project Draft Short name": "Child Protection East Africa", "Budget Range": "1M$"}', 'A project for child protection along the East Africa route.', 'approved', NOW() - INTERVAL '30 days', NOW() - INTERVAL '2 days');

INSERT INTO proposal_donors (proposal_id, donor_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12');
INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12');
INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'draft', NOW() - INTERVAL '30 days');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'in_review', NOW() - INTERVAL '20 days');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'submission', NOW() - INTERVAL '10 days');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'submitted', NOW() - INTERVAL '5 days');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'approved', NOW() - INTERVAL '2 days');

-- Proposal 3 (by Charlie, Team Bravo)
INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'unhcr_proposal_template.json', '{"Project Draft Short name": "Venezuela Documentation", "Budget Range": "250k$"}', 'A project to provide documentation to refugees from Venezuela.', 'draft', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day');

INSERT INTO proposal_donors (proposal_id, donor_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12');
INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES ('p0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'draft', NOW() - INTERVAL '2 days');

-- Insert Knowledge Cards
INSERT INTO knowledge_cards (id, title, summary, status, donor_id) VALUES
('k0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'USAID Funding Priorities', 'A summary of USAID''s key funding areas for the current fiscal year.', 'published', 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
INSERT INTO knowledge_card_references (knowledge_card_id, url, reference_type) VALUES ('k0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'https://www.usaid.gov/work-usaid/get-grant-or-contract/funding-opportunities', 'Official Website');

INSERT INTO knowledge_cards (id, title, summary, status, outcome_id) VALUES
('k0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Best Practices in Child Protection', 'A collection of best practices from various field operations.', 'published', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12');

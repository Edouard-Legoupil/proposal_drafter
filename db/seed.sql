


-- Clear existing data
TRUNCATE TABLE teams, users, donors, outcomes, field_contexts, proposals, proposal_donors, proposal_outcomes, proposal_field_contexts, proposal_peer_reviews, proposal_status_history, knowledge_cards, knowledge_card_references RESTART IDENTITY CASCADE;

-- Insert Teams with properly formatted UUIDs
INSERT INTO teams (id, name) VALUES
(gen_random_uuid(), 'DRRM'),
(gen_random_uuid(), 'HQ Protection'),
(gen_random_uuid(), 'Test');

INSERT INTO teams  (id, name) VALUES
(gen_random_uuid(), 'Brussels Donor Group'),
(gen_random_uuid(), 'DRRM Donor Group 1'),
(gen_random_uuid(), 'DRRM Donor Group 2'),
(gen_random_uuid(), 'DRRM Donor Group 3'),
(gen_random_uuid(), 'DRRM Donor Group 4'),
(gen_random_uuid(), 'DRRM Donor Group 5'),
(gen_random_uuid(), 'DRRM Donor Group 6'),
(gen_random_uuid(), 'DRRM Donor Group 1'),
(gen_random_uuid(), 'DRRM Donor Group 4'),
(gen_random_uuid(), 'IRU - Income Recording');


-- -- Insert Donors
INSERT INTO donors (id, account_id, name, country, donor_group) VALUES
(gen_random_uuid(), 'IGOV-EU-10723', 'EU ECHO', 'EU', 'Brussels Donor Group'),
(gen_random_uuid(), 'UN-CERF-10751', 'CERF Rapid Response', 'UN', 'DRRM Donor Group 5'),
(gen_random_uuid(), 'UN-CERF-10752', 'CERF Underfunded Emergencies', 'UN', 'DRRM Donor Group 5'),
(gen_random_uuid(), 'GOV-JP-10631', 'Japan - Ministry of Foreign Affairs HAD', 'Japan', 'DRRM Donor Group 4'),
(gen_random_uuid(), 'GOV-JP-10632', 'Japan - Ministry of Foreign Affairs EGA', 'Japan', 'DRRM Donor Group 4'),
(gen_random_uuid(), 'GOV-JP-10636', 'Japan - Ministry of Foreign Affairs Year-end Supplementary Budget', 'Japan', 'DRRM Donor Group 4'),
(gen_random_uuid(), 'GOV-US-10711', 'United States of America - Population Refugee & Migration', 'USA', 'DRRM Donor Group 3'),
(gen_random_uuid(), 'GOV-DE-10524', 'Germany - Federal Foreign Office - Division for Humanitarian Assistance', 'Germany', 'DRRM Donor Group 6'),
(gen_random_uuid(), 'GOV-GB-10600', 'United Kingdom - Foreign, Commonwealth and Development Office (FCDO)', 'United Kingdom', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-SE-10700', 'Sweden - Ministry for Foreign Affairs', 'Sweden', 'DRRM Donor Group 2'),
(gen_random_uuid(), 'GOV-NO-10672', 'Norway - Ministry for Foreign Affairs', 'Norway', 'DRRM Donor Group 2'),
(gen_random_uuid(), 'GOV-DK-10531', 'Denmark - Ministry of Foreign Affairs', 'Denmark', 'DRRM Donor Group 2'),
(gen_random_uuid(), 'GOV-CA-10496', 'Canada - Department of Foreign Affairs, Trade and Development', 'Canada', 'DRRM Donor Group 3'),
(gen_random_uuid(), 'GOV-NL-10665', 'Netherlands - Ministry of Foreign Affairs Humanitarian Aid Division', 'Netherlands', 'DRRM Donor Group 6'),
(gen_random_uuid(), 'IGOV-EU-10726', 'EU HOME', 'EU', 'Brussels Donor Group'),
(gen_random_uuid(), 'GOV-CH-10504', 'Switzerland - Swiss Agency for Development and Cooperation', 'Switzerland', 'DRRM Donor Group 6'),
(gen_random_uuid(), 'GOV-FR-10589', 'France - Ministry of Foreign Affairs', 'France', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'UN-UNHQ-10780', 'United Nations Regular Budget', 'UN', 'DRRM Donor Group 5'),
(gen_random_uuid(), 'GOV-AU-10470', 'Australia - Department of Foreign Affairs & Trade', 'Australia', 'DRRM Donor Group 4'),
(gen_random_uuid(), 'GOV-SE-10701', 'Sweden - Swedish International Development Cooperation Agency', 'Sweden', 'DRRM Donor Group 2'),
(gen_random_uuid(), 'GOV-FI-10588', 'Finland - Ministry of Foreign Affairs', 'Finland', 'DRRM Donor Group 2'),
(gen_random_uuid(), 'GOV-KW-10645', 'State of Kuwait - Kuwait', 'Kuwait', 'DRRM Donor Group 3'),
(gen_random_uuid(), 'IGOV-EU-10737', 'EU INTPA NDICI', 'EU', 'Brussels Donor Group'),
(gen_random_uuid(), 'IGOV-EU-10724', 'EU DEVCO/INTPA DCI', 'EU', 'Brussels Donor Group'),
(gen_random_uuid(), 'GOV-IE-10613', 'Ireland - Irish Aid', 'Ireland', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-BE-10480', 'Belgium - Ministry of Foreign Affairs - Humanitarian Aid Unit', 'Belgium', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-NL-10670', 'Netherlands - MFA Migr&Dev Gp–Developmnt Financing', 'Netherlands', 'DRRM Donor Group 6'),
(gen_random_uuid(), 'GOV-KR-10643', 'Republic of Korea - Ministry of Foreign Affairs', 'Republic of Korea', 'DRRM Donor Group 4'),
(gen_random_uuid(), 'GOV-IT-10620', 'Italy - Ministry of Foreign Affairs - DGCS', 'Italy', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-LU-10652', 'Grand Duchy of Luxembourg - Ministry of Foreign Affairs Cooperation and Humanitarian Aid', 'Luxembourg', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-IT-10625', 'Italy - Ministry of Foreign Affairs - DGIT', 'Italy', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-ES-10539', 'Spain - AECID - Humanitarian Action Office', 'Spain', 'DRRM Donor Group 1'),
(gen_random_uuid(), 'GOV-DE-10525', 'Germany - Federal Foreign Office - Cultural Department', 'Germany', 'DRRM Donor Group 6'),
(gen_random_uuid(), 'GOV-NO-11789', 'Norway - Ministry of Development - Norwegian Agency for Development Cooperation (Norad)', 'Norway', 'DRRM Donor Group 2'),
(gen_random_uuid(), 'GOV-SA-10693', 'Kingdom of Saudi Arabia - Saudi Arabia through OCHA', 'Saudi Arabia', 'DRRM Donor Group 3'),
(gen_random_uuid(), 'IGOV-EU-10727', 'EU EEAS Instrument contributing to Stability and Peace', 'EU', 'Brussels Donor Group'),
(gen_random_uuid(), 'GOV-AT-10476', 'Austria - Austrian Development Agency', 'Austria', 'DRRM Donor Group 6'),
(gen_random_uuid(), 'GOV-SA-10694', 'Kingdom of Saudi Arabia - King Salman Hum Aid & Relief Center', 'Saudi Arabia', 'DRRM Donor Group 3'),
(gen_random_uuid(), 'GOV-QA-10687', 'Qatar - Qatar Fund For Development', 'Qatar', 'DRRM Donor Group 3');


INSERT INTO field_contexts (id, name, category, geographic_coverage) VALUES
(gen_random_uuid(),  'Afghanistan', 'Country', 'One Country Operation'),
(gen_random_uuid(),  'Algeria', 'Country', 'One Country Operation'),

(gen_random_uuid(),  'Zimbabwe', 'Country', 'One Country Operation');

-- Insert Field Contexts (Countries)
INSERT INTO field_contexts (id, title, name, category, geographic_coverage) VALUES
(gen_random_uuid(), 'Afghanistan Situation', 'Afghanistan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Algeria Situation', 'Algeria', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Angola Situation', 'Angola', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Argentina Situation', 'Argentina', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Bangladesh Situation', 'Bangladesh', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Brazil Situation', 'Brazil', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Burkina Faso Situation', 'Burkina Faso', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Burundi Situation', 'Burundi', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Cameroon Situation', 'Cameroon', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Central African Republic Situation', 'Central African Republic', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Chad Situation', 'Chad', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Colombia Situation', 'Colombia', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Costa Rica Situation', 'Costa Rica', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Côte d''Ivoire Situation', 'Côte d''Ivoire', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Democratic Republic of the Congo Situation', 'Democratic Republic of the Congo', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Ecuador Situation', 'Ecuador', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Egypt Situation', 'Egypt', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'El Salvador Situation', 'El Salvador', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Ethiopia Situation', 'Ethiopia', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Guatemala Situation', 'Guatemala', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Honduras Situation', 'Honduras', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'India Situation', 'India', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Indonesia Situation', 'Indonesia', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Iraq Situation', 'Iraq', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Islamic Republic of Iran Situation', 'Islamic Republic of Iran', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Jordan Situation', 'Jordan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Kazakhstan Situation', 'Kazakhstan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Kenya Situation', 'Kenya', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Lebanon Situation', 'Lebanon', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Libya Situation', 'Libya', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Malawi Situation', 'Malawi', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Malaysia Situation', 'Malaysia', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Mali Situation', 'Mali', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Mauritania Situation', 'Mauritania', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Mexico Situation', 'Mexico', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Mozambique Situation', 'Mozambique', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Myanmar Situation', 'Myanmar', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Niger Situation', 'Niger', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Nigeria Situation', 'Nigeria', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Pakistan Situation', 'Pakistan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Panama Situation', 'Panama', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Peru Situation', 'Peru', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Republic of Moldova Situation', 'Republic of Moldova', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Republic of the Congo Situation', 'Republic of the Congo', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Republic of Türkiye Situation', 'Republic of Türkiye', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Rwanda Situation', 'Rwanda', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Somalia Situation', 'Somalia', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'South Africa Situation', 'South Africa', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'South Sudan Situation', 'South Sudan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Sudan Situation', 'Sudan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Syrian Arab Republic Situation', 'Syrian Arab Republic', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Tajikistan Situation', 'Tajikistan', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Thailand Situation', 'Thailand', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Uganda Situation', 'Uganda', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Ukraine Situation', 'Ukraine', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'United Republic of Tanzania Situation', 'United Republic of Tanzania', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Venezuela (Bolivarian Republic of) Situation', 'Venezuela (Bolivarian Republic of)', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Yemen Situation', 'Yemen', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Zambia Situation', 'Zambia', 'Country', 'One Country Operation'),
(gen_random_uuid(), 'Zimbabwe Situation', 'Zimbabwe', 'Country', 'One Country Operation');

-- -- Insert Outcomes with pre-defined UUIDs for consistency
-- INSERT INTO outcomes (id, name) VALUES
-- (gen_random_uuid(), 'OA1-Access/Documentation'),
-- (gen_random_uuid(), 'OA2-Status'),
-- (gen_random_uuid(), 'OA3-Protection Policy'),
-- (gen_random_uuid(), 'OA4-GBV'),
-- (gen_random_uuid(), 'OA5-Child protection'),
-- (gen_random_uuid(), 'OA6-Justice'),
-- (gen_random_uuid(), 'OA7-Community'),
-- (gen_random_uuid(), 'OA8-Well-Being'),
-- (gen_random_uuid(), 'OA9-Housing'),
-- (gen_random_uuid(), 'OA10-Health'),
-- (gen_random_uuid(), 'OA11-Education'),
-- (gen_random_uuid(), 'OA12-WASH'),
-- (gen_random_uuid(), 'OA13-Livelihoods'),
-- (gen_random_uuid(), 'OA14-Return'),
-- (gen_random_uuid(), 'OA15-Resettlement'),
-- (gen_random_uuid(), 'OA16-Integrate');

-- -- Insert Users with consistent UUIDs
-- Insert Users with consistent UUIDs
INSERT INTO users (id, email, password, name, team_id, created_by, updated_by) VALUES
('a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2c', 'test_user@unhcr.org', '$2b$12$DwbvI.0M9c.uAiurT9zL9eR3u8vjP.yU/b4L6f/Yt2xY.gC6wzBGS', 'Test User', (SELECT id FROM teams WHERE name = 'Test' LIMIT 1), 'a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2c', 'a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2c');

-- Insert a proposal with pre_submission status for testing
INSERT INTO proposals (id, user_id, created_by, updated_by, template_name, form_data, project_description, status) VALUES
('a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2d', 'a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2c', 'a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2c', 'a4e89f89-8f47-4d74-9a2c-9d6f3e8a6a2c', 'unhcr_proposal_template.json', '{"Project Draft Short name": "Pre-submission Project", "Budget Range": "100k$"}', 'A project for testing the pre-submission stage.', 'pre_submission');



-- -- Insert Donors with pre-defined UUIDs
-- INSERT INTO donors (id, account_id, name, country, donor_group) VALUES
-- ('00000000-0000-4000-8000-000000000011', 'GOV-US-10711', 'United States of America - Population Refugee & Migration', 'USA', 'DRRM Donor Group 3'),
-- ('00000000-0000-4000-8000-000000000012', 'GOV-DE-10524', 'Germany - Federal Foreign Office - Division for Humanitarian Assistance', 'Germany', 'DRRM Donor Group 6'),
-- ('00000000-0000-4000-8000-000000000045', 'GOV-QA-10687', 'Qatar - Qatar Fund For Development', 'Qatar', 'DRRM Donor Group 3');

-- -- Insert Field Contexts with pre-defined UUIDs (including Colombia and Ukraine)
-- INSERT INTO field_contexts (id, title, name, category, geographic_coverage) VALUES
-- ('00000000-0000-4000-8000-000000000101', 'Afghanistan Situation', 'Afghanistan', 'Country', 'One Country Operation'),
-- ('00000000-0000-4000-8000-000000000112', 'Colombia Situation', 'Colombia', 'Country', 'One Country Operation'),
-- ('00000000-0000-4000-8000-000000000154', 'Ukraine Situation', 'Ukraine', 'Country', 'One Country Operation'),
-- ('00000000-0000-4000-8000-000000000165', 'Zimbabwe Situation', 'Zimbabwe', 'Country', 'One Country Operation');

-- Link proposals (using the same pattern for UUID consistency)
-- DO $$
-- DECLARE
--     proposal1_id uuid := '00000000-0000-4000-8000-000000000201';
--     proposal2_id uuid := '00000000-0000-4000-8000-000000000202';
--     alice_id uuid := 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
--     bob_id uuid := 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
--     donor1_id uuid := '00000000-0000-4000-8000-000000000011';
--     donor2_id uuid := '00000000-0000-4000-8000-000000000012';
--     outcome1_id uuid := 'cccccccc-cccc-cccc-8ccc-cccccccccccd'; -- OA9-Housing
--     outcome2_id uuid := '88888888-8888-8888-8888-888888888888'; -- OA5-Child protection
--     context1_id uuid := '00000000-0000-4000-8000-000000000112'; -- Colombia
--     context2_id uuid := '00000000-0000-4000-8000-000000000154'; -- Ukraine
-- BEGIN
--     -- Insert Proposal 1
--     INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
--     (proposal1_id, alice_id, 'unhcr_proposal_template.json', '{"Project Draft Short name": "Colombia Shelter Project", "Budget Range": "500k$"}', 'A project to provide shelter for displaced persons in Colombia.', 'in_review', NOW() - INTERVAL '10 days', NOW() - INTERVAL '5 days');

--     INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (proposal1_id, donor1_id);
--     INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (proposal1_id, outcome1_id);
--     INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (proposal1_id, context1_id);
--     INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, status) VALUES (proposal1_id, bob_id, 'pending');
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal1_id, 'draft', NOW() - INTERVAL '10 days');
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal1_id, 'in_review', NOW() - INTERVAL '5 days');

--     -- Insert Proposal 2
--     INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
--     (proposal2_id, bob_id, 'unhcr_proposal_template.json', '{"Project Draft Short name": "Child Protection Ukraine", "Budget Range": "1M$"}', 'A project for child protection in Ukraine.', 'approved', NOW() - INTERVAL '30 days', NOW() - INTERVAL '2 days');

--     INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (proposal2_id, donor2_id);
--     INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (proposal2_id, outcome2_id);
--     INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (proposal2_id, context2_id);
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal2_id, 'draft', NOW() - INTERVAL '30 days');
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal2_id, 'in_review', NOW() - INTERVAL '20 days');
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal2_id, 'submission', NOW() - INTERVAL '10 days');
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal2_id, 'submitted', NOW() - INTERVAL '5 days');
--     INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal2_id, 'approved', NOW() - INTERVAL '2 days');

--     -- Insert Proposal 3 for Pre-Submission view
--     DECLARE
--         proposal3_id uuid := '00000000-0000-4000-8000-000000000203';
--         charlie_id uuid := 'cccccccc-cccc-4ccc-8ccc-cccccccccccc';
--     BEGIN
--         INSERT INTO proposals (id, user_id, template_name, form_data, project_description, status, created_at, updated_at) VALUES
--         (proposal3_id, alice_id, 'unhcr_proposal_template.json', '{"Project Draft Short name": "Zimbabwe Livelihoods", "Budget Range": "250k$"}', 'A project for livelihoods in Zimbabwe.', 'submission', NOW() - INTERVAL '3 days', NOW() - INTERVAL '1 day');

--         INSERT INTO proposal_donors (proposal_id, donor_id) VALUES (proposal3_id, donor1_id);
--         INSERT INTO proposal_outcomes (proposal_id, outcome_id) VALUES (proposal3_id, outcome2_id);
--         INSERT INTO proposal_field_contexts (proposal_id, field_context_id) VALUES (proposal3_id, '00000000-0000-4000-8000-000000000165');
--         INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, status, section_name, review_text) VALUES (proposal3_id, bob_id, 'completed', 'Executive Summary', 'This section needs more detail on the target population.');
--         INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal3_id, 'draft', NOW() - INTERVAL '3 days');
--         INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal3_id, 'in_review', NOW() - INTERVAL '2 days');
--         INSERT INTO proposal_status_history (proposal_id, status, created_at) VALUES (proposal3_id, 'submission', NOW() - INTERVAL '1 day');
--     END;
-- END $$;
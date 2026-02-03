


-- Clear existing data
TRUNCATE TABLE teams, users, donors, outcomes, field_contexts, proposals, proposal_donors, proposal_outcomes, proposal_field_contexts, proposal_peer_reviews, proposal_status_history, knowledge_cards, knowledge_card_references RESTART IDENTITY CASCADE;

-- Insert Teams with properly formatted UUIDs
INSERT INTO teams (id, name) VALUES
(gen_random_uuid(), 'DRRM'),
(gen_random_uuid(), 'HQ Protection'),
(gen_random_uuid(), 'Test');

INSERT INTO donor_groups (id, name) VALUES
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
(gen_random_uuid(), 'IGOV-EU-10723', 'EU ECHO', 'EU', 'Brussels Donor Group');

INSERT INTO field_contexts (id, name, category, geographic_coverage) VALUES
(gen_random_uuid(),  'Afghanistan', 'Country', 'One Country Operation'),
(gen_random_uuid(),  'Algeria', 'Country', 'One Country Operation'),

(gen_random_uuid(),  'Zimbabwe', 'Country', 'One Country Operation');

-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: admin
--

INSERT INTO public.teams VALUES ('a44199b7-06b2-473d-ab80-87a419515b61', 'UNHCR');
INSERT INTO public.teams VALUES ('91e1f13b-a25e-4b71-b850-25dfa2122b5e', 'UNICEF');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: admin
--

INSERT INTO public.users VALUES ('f1b9b9b0-9b9b-4b9b-8b9b-9b9b9b9b9b9b', 'test_user@unhcr.org', 'password', 'Test User', 'a44199b7-06b2-473d-ab80-87a419515b61', NULL, false, '2024-05-13 14:00:23.014619+00', '2024-05-13 14:00:23.014619+00');


INSERT INTO roles (name) VALUES
  ('proposal writer'),
  ('knowledge manager donors'),
  ('knowledge manager outcome'),
  ('knowledge manager field context'),
  ('project reviewer');
--
-- PostgreSQL database dump complete
--

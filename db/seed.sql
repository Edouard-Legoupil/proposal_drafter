--
-- PostgreSQL database dump
--

-- Dumped from database version 13.5 (Debian 13.5-0+deb11u1)
-- Dumped by pg_dump version 13.5 (Debian 13.5-0+deb11u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
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

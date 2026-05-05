


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


INSERT INTO field_contexts (id, name, category, geographic_coverage) VALUES
(gen_random_uuid(),  'Global', 'Global Coverage', 'Global Coverage');

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


-- ============================================================================
--  Expanded Seed Data for Incident Analysis + Qualification
-- ============================================================================
-- PURPOSE
--   Comprehensive optional seed data for the schema extension previously created.
--   This file seeds:
--     1) Qualification rule sets
--     2) Full proposal-template qualification rules
--     3) Full knowledge-card-template qualification rules
--     4) Representative qualification scenarios
--
-- PREREQUISITES
--   - Run AFTER database-setup.sql
--
-- REQUIRED MANUAL SUBSTITUTIONS
--   Replace the placeholders below before running:
--     <ADMIN_USER_ID>
--     <DEFAULT_TEAM_ID>          -- optional, may be left NULL if not used in scenario metadata
--
-- NOTES
--   - Uses ON CONFLICT DO NOTHING for idempotency.
--   - Rule codes are stable and intended to be referenced by the API/policy engine.
-- ============================================================================

BEGIN;

-- --------------------------------------------------------------------------
-- 0) OPTIONAL SAFETY CHECKS (COMMENT OUT IF YOU DO NOT WANT FAIL-FAST BEHAVIOR)
-- --------------------------------------------------------------------------
DO $$
DECLARE
    admin_user UUID := '<ADMIN_USER_ID>'::uuid;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = admin_user) THEN
        RAISE EXCEPTION 'Seed failed: <ADMIN_USER_ID> does not exist in users table.';
    END IF;
END$$;


BEGIN;

-- 1) Delete rule evaluations and dependent artifacts (if any exist)
DELETE FROM qualification_rule_evaluations;
DELETE FROM qualification_waivers;

-- 2) Delete qualification rules
DELETE FROM qualification_rules;

-- 3) Delete qualification rule sets
DELETE FROM qualification_rule_sets
WHERE name IN (
    'Proposal Template Qualification Rules',
    'Knowledge Card Template Qualification Rules'
);

COMMIT;



-- --------------------------------------------------------------------------
-- 1) RULE SETS
-- --------------------------------------------------------------------------
INSERT INTO qualification_rule_sets (
    name,
    template_type,
    version_label,
    is_active,
    description,
    created_by,
    updated_by
)
VALUES
(
    'Proposal Template Qualification Rules',
    'proposal',
    'v1',
    TRUE,
    'Default UAT-to-Prod qualification policy for proposal templates. Covers critical blockers, coverage thresholds, structure, review coverage, quality scoring, editing burden, regulated language safety, and scenario robustness.',
    '<ADMIN_USER_ID>'::uuid,
    '<ADMIN_USER_ID>'::uuid
),
(
    'Knowledge Card Template Qualification Rules',
    'knowledge_card',
    'v1',
    TRUE,
    'Default UAT-to-Prod qualification policy for knowledge-card templates. Covers critical blockers, traceability, freshness, metadata quality, duplication, generic content, source coverage, and downstream usability.',
    '<ADMIN_USER_ID>'::uuid,
    '<ADMIN_USER_ID>'::uuid
)
ON CONFLICT (name) DO NOTHING;

-- --------------------------------------------------------------------------
-- 2) PROPOSAL TEMPLATE RULES
-- --------------------------------------------------------------------------
WITH proposal_ruleset AS (
    SELECT id
    FROM qualification_rule_sets
    WHERE name = 'Proposal Template Qualification Rules'
    LIMIT 1
)
INSERT INTO qualification_rules (
    rule_set_id,
    rule_code,
    rule_name,
    category,
    severity,
    applies_to,
    evaluation_mode,
    metric_name,
    comparator,
    threshold_numeric,
    threshold_json,
    weight,
    required,
    description,
    remediation_guidance,
    is_active
)
SELECT 
  rule_set_id,
  rule_code,
  rule_name,
  category,
  severity,
  applies_to::managed_template_type,
  evaluation_mode,
  metric_name,
  comparator,
  threshold_numeric,
  threshold_json,
  weight::numeric,
  required,
  description,
  remediation_guidance,
  is_active
FROM (
    VALUES
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_NO_UNRESOLVED_P0',
        'No unresolved P0 incidents',
        'blocker',
        'blocker',
        'proposal',
        'hard_blocker',
        'unresolved_p0_count',
        '=',
        0,
        NULL::jsonb,
        NULL,
        TRUE,
        'Any unresolved P0 incident in UAT disqualifies a proposal template from promotion.',
        'Resolve all critical incidents and re-run the qualification cycle.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_NO_UNSUPPORTED_REGULATED_LANGUAGE',
        'No unsupported regulated language',
        'blocker',
        'blocker',
        'proposal',
        'hard_blocker',
        'unsupported_regulated_claim_count',
        '=',
        0,
        '{"domains": ["compliance", "security", "legal", "financial"]}'::jsonb,
        NULL,
        TRUE,
        'No unsupported regulated-domain statements may appear in UAT outputs.',
        'Strengthen grounding and validation for compliance, security, legal, and financial sections.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_MANDATORY_SECTIONS',
        'Mandatory section completeness',
        'coverage',
        'blocker',
        'proposal',
        'hard_blocker',
        'mandatory_section_missing_count',
        '=',
        0,
        '{"scope": "all_outputs"}'::jsonb,
        NULL,
        TRUE,
        'No mandatory section may be missing from any evaluated proposal output.',
        'Fix template structure and section planning before promotion.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_MIN_SAMPLE_SIZE',
        'Minimum UAT sample size',
        'coverage',
        'major',
        'proposal',
        'threshold',
        'uat_sample_size',
        '>=',
        10,
        '{"unit": "proposals"}'::jsonb,
        NULL,
        TRUE,
        'At least 10 UAT proposal outputs must be evaluated before qualification.',
        'Generate additional UAT proposals and collect reviews.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_MIN_SCENARIO_COUNT',
        'Minimum distinct scenario coverage',
        'coverage',
        'major',
        'proposal',
        'threshold',
        'distinct_scenario_count',
        '>=',
        3,
        '{"unit": "scenarios"}'::jsonb,
        NULL,
        TRUE,
        'At least 3 distinct scenarios must be executed for each proposal template qualification run.',
        'Add missing donor, geography, and field-context scenarios.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_SCENARIO_ARCHETYPE_PASS_RATE',
        'Required scenario archetypes must pass',
        'coverage',
        'major',
        'proposal',
        'threshold',
        'scenario_archetype_pass_rate_pct',
        '>=',
        100,
        '{"required_archetypes": ["standard", "high_risk", "multi_context"]}'::jsonb,
        NULL,
        TRUE,
        'All required scenario archetypes must pass qualification thresholds.',
        'Address scenario-specific defects and re-run archetype coverage.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_AVG_SCORE',
        'Average weighted quality score',
        'scorecard',
        'major',
        'proposal',
        'threshold',
        'avg_quality_score',
        '>=',
        85,
        '{"formula": "100 - (40*P0 + 15*P1 + 5*P2 + 1*P3) normalized per output"}'::jsonb,
        30,
        TRUE,
        'Average weighted quality score across evaluated outputs must be at least 85.',
        'Reduce P1/P2 issue frequency and improve section completeness.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_MIN_RUN_SCORE',
        'Lowest individual run score',
        'scorecard',
        'major',
        'proposal',
        'threshold',
        'min_run_score',
        '>=',
        70,
        '{"unit": "proposal_output"}'::jsonb,
        10,
        TRUE,
        'No individual proposal output may score below 70.',
        'Investigate scenario-specific failures and remediate low-performing sections.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_P1_SECTION_REPEAT',
        'Repeated P1 in same section',
        'threshold',
        'major',
        'proposal',
        'threshold',
        'max_repeated_p1_same_section',
        '<=',
        2,
        '{"scope": "per_section_per_run"}'::jsonb,
        10,
        TRUE,
        'A single section may not accumulate more than 2 repeated P1 defects in one qualification run.',
        'Redesign the failing section or add section-specific constraints.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_P1_RATE',
        'P1 rate threshold',
        'threshold',
        'major',
        'proposal',
        'threshold',
        'p1_rate_pct',
        '<=',
        10,
        '{"denominator": "reviewed_sections"}'::jsonb,
        10,
        TRUE,
        'P1 incident rate must not exceed 10 percent of reviewed sections.',
        'Reduce major structural and content-gap issues.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_REVIEW_COVERAGE',
        'Proposal review coverage',
        'review',
        'major',
        'proposal',
        'threshold',
        'review_coverage_pct',
        '>=',
        80,
        '{"denominator": "evaluated_outputs"}'::jsonb,
        8,
        TRUE,
        'At least 80 percent of generated proposal outputs must receive peer review.',
        'Increase reviewer participation before promotion.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_CRITICAL_SECTION_REVIEW_COVERAGE',
        'Critical sections reviewed',
        'review',
        'major',
        'proposal',
        'threshold',
        'critical_section_review_coverage_pct',
        '>=',
        100,
        '{"critical_sections": ["compliance", "security", "budget", "implementation_plan"]}'::jsonb,
        8,
        TRUE,
        'All critical sections must be reviewed in UAT before promotion.',
        'Ensure all critical sections receive reviewer coverage.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_MIN_REVIEWERS_PER_CRITICAL_SECTION',
        'Minimum reviewers for critical sections',
        'review',
        'major',
        'proposal',
        'threshold',
        'min_reviewers_per_critical_section',
        '>=',
        2,
        '{"critical_sections": ["compliance", "security", "budget", "implementation_plan"]}'::jsonb,
        6,
        TRUE,
        'Each critical section must be reviewed by at least two reviewers.',
        'Assign more reviewers for high-risk sections.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_ACCEPTANCE_RATE',
        'Business acceptance rate',
        'business',
        'major',
        'proposal',
        'threshold',
        'acceptance_rate_pct',
        '>=',
        80,
        '{"definition": "accepted with no major revision"}'::jsonb,
        8,
        TRUE,
        'At least 80 percent of reviewed outputs must be accepted with no major revision.',
        'Improve content quality and reduce manual rewrite burden.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_FORMATTING_PASS_RATE',
        'Formatting pass rate',
        'quality',
        'minor',
        'proposal',
        'threshold',
        'formatting_pass_rate_pct',
        '>=',
        95,
        '{"scope": "non_critical_formatting"}'::jsonb,
        3,
        TRUE,
        'Formatting/style pass rate for non-critical checks must be at least 95 percent.',
        'Improve output formatting and post-processing rules.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_MEDIAN_MANUAL_REWRITE_BURDEN',
        'Median manual rewrite burden',
        'quality',
        'major',
        'proposal',
        'threshold',
        'median_manual_rewrite_pct',
        '<=',
        20,
        '{"scope": "critical_sections_only"}'::jsonb,
        7,
        TRUE,
        'Median manual rewrite burden in critical sections must be 20 percent or lower.',
        'Improve content planning and section-specific grounding.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_PLACEHOLDER_RESOLUTION',
        'No unresolved placeholders',
        'quality',
        'major',
        'proposal',
        'hard_blocker',
        'unresolved_placeholder_count',
        '=',
        0,
        '{"examples": ["TODO", "TBD", "<insert>"]}'::jsonb,
        NULL,
        TRUE,
        'No unresolved placeholders may remain in evaluated proposal outputs.',
        'Add final validation to block unresolved placeholder tokens.',
        TRUE
    ),
    (
        (SELECT id FROM proposal_ruleset),
        'PROPOSAL_EMPTY_MANDATORY_SECTION_COUNT',
        'No empty mandatory sections',
        'quality',
        'blocker',
        'proposal',
        'hard_blocker',
        'empty_mandatory_section_count',
        '=',
        0,
        '{"scope": "all_outputs"}'::jsonb,
        NULL,
        TRUE,
        'Mandatory sections may not be present but empty.',
        'Ensure section generation always emits substantive content.',
        TRUE
    )
) AS seed_rows (
    rule_set_id,
    rule_code,
    rule_name,
    category,
    severity,
    applies_to,
    evaluation_mode,
    metric_name,
    comparator,
    threshold_numeric,
    threshold_json,
    weight,
    required,
    description,
    remediation_guidance,
    is_active
)
ON CONFLICT (rule_set_id, rule_code) DO NOTHING;

-- --------------------------------------------------------------------------
-- 3) KNOWLEDGE-CARD TEMPLATE RULES
-- --------------------------------------------------------------------------
WITH kc_ruleset AS (
    SELECT id
    FROM qualification_rule_sets
    WHERE name = 'Knowledge Card Template Qualification Rules'
    LIMIT 1
)
INSERT INTO qualification_rules (
    rule_set_id,
    rule_code,
    rule_name,
    category,
    severity,
    applies_to,
    evaluation_mode,
    metric_name,
    comparator,
    threshold_numeric,
    threshold_json,
    weight,
    required,
    description,
    remediation_guidance,
    is_active
)
SELECT 
  rule_set_id,
  rule_code,
  rule_name,
  category,
  severity,
  applies_to::managed_template_type,
  evaluation_mode,
  metric_name,
  comparator,
  threshold_numeric,
  threshold_json,
  weight::numeric,
  required,
  description,
  remediation_guidance,
  is_active
FROM (
    VALUES
    (
        (SELECT id FROM kc_ruleset),
        'KC_NO_UNRESOLVED_P0',
        'No unresolved P0 incidents',
        'blocker',
        'blocker',
        'knowledge_card',
        'hard_blocker',
        'unresolved_p0_count',
        '=',
        0,
        NULL::jsonb,
        NULL,
        TRUE,
        'Any unresolved Data Integrity, Source Error, or Critical Omission blocks promotion.',
        'Resolve source, integrity, and omission defects before re-qualification.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_MIN_SAMPLE_SIZE',
        'Minimum UAT knowledge-card count',
        'coverage',
        'major',
        'knowledge_card',
        'threshold',
        'uat_sample_size',
        '>=',
        20,
        '{"unit": "knowledge_cards"}'::jsonb,
        NULL,
        TRUE,
        'At least 20 UAT knowledge cards must be evaluated before qualification.',
        'Generate additional UAT cards and collect reviewer feedback.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_MIN_SCENARIO_COUNT',
        'Minimum coverage groups',
        'coverage',
        'major',
        'knowledge_card',
        'threshold',
        'distinct_scenario_count',
        '>=',
        3,
        '{"unit": "coverage_groups"}'::jsonb,
        NULL,
        TRUE,
        'At least 3 distinct coverage groups are required.',
        'Add donor, outcome, and field-context coverage to the UAT set.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_CRITICAL_TRACEABILITY',
        'Critical claim traceability',
        'traceability',
        'blocker',
        'knowledge_card',
        'hard_blocker',
        'critical_claim_traceability_pct',
        '>=',
        100,
        '{"scope": "critical_claims"}'::jsonb,
        NULL,
        TRUE,
        'All critical claims must be traceable to valid sources.',
        'Fix reference linking and evidence extraction for critical content.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_FACTUAL_TRACEABILITY',
        'Overall factual traceability',
        'traceability',
        'major',
        'knowledge_card',
        'threshold',
        'traceable_claim_ratio_pct',
        '>=',
        95,
        '{"scope": "all_factual_claims"}'::jsonb,
        20,
        TRUE,
        'At least 95 percent of factual claims must be traceable.',
        'Increase provenance coverage and improve grounding.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_TRACEABILITY_GAP_RATE',
        'Traceability gap rate',
        'traceability',
        'major',
        'knowledge_card',
        'threshold',
        'traceability_gap_rate_pct',
        '<=',
        5,
        '{"source": "knowledge_card_reviews"}'::jsonb,
        8,
        TRUE,
        'Traceability gap defect rate must be 5 percent or lower.',
        'Add source metadata and citation coverage checks.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_REFERENCE_COVERAGE',
        'Reference coverage',
        'traceability',
        'major',
        'knowledge_card',
        'threshold',
        'cards_with_references_pct',
        '>=',
        95,
        '{"definition": "share_of_cards_with_linked_references"}'::jsonb,
        8,
        TRUE,
        'At least 95 percent of evaluated knowledge cards must have linked references.',
        'Ensure every card includes sufficient linked references.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_OUTDATED_INFO_RATE',
        'Outdated information rate',
        'freshness',
        'major',
        'knowledge_card',
        'threshold',
        'outdated_information_rate_pct',
        '<=',
        5,
        '{"source": "knowledge_card_reviews"}'::jsonb,
        8,
        TRUE,
        'Outdated-information defect rate must be 5 percent or lower.',
        'Strengthen freshness checks and source recency governance.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_STALE_SOURCE_WITHOUT_RECENCY_METADATA',
        'No stale source without recency metadata',
        'freshness',
        'major',
        'knowledge_card',
        'hard_blocker',
        'stale_source_without_recency_metadata_count',
        '=',
        0,
        '{"requires": ["scraped_at", "source_date_or_equivalent"]}'::jsonb,
        NULL,
        TRUE,
        'No stale source may be used without recency metadata or freshness control.',
        'Enforce source-date metadata and freshness validation.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_DUPLICATE_RATE',
        'Duplicate content rate',
        'quality',
        'major',
        'knowledge_card',
        'threshold',
        'duplicate_content_rate_pct',
        '<=',
        10,
        '{"source": "knowledge_card_reviews"}'::jsonb,
        7,
        TRUE,
        'Duplicate content rate must be 10 percent or lower.',
        'Improve deduplication and content specificity.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_GENERIC_RATE',
        'Generic content rate',
        'quality',
        'major',
        'knowledge_card',
        'threshold',
        'generic_content_rate_pct',
        '<=',
        20,
        '{"source": "knowledge_card_reviews"}'::jsonb,
        7,
        TRUE,
        'Generic content rate must be 20 percent or lower.',
        'Strengthen template specificity and evidence usage.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_AVG_REVIEWER_RATING',
        'Average reviewer rating',
        'quality',
        'major',
        'knowledge_card',
        'threshold',
        'avg_reviewer_rating',
        '>=',
        4,
        '{"scale": "1_to_5"}'::jsonb,
        8,
        TRUE,
        'Average reviewer rating must be at least 4 out of 5.',
        'Improve card usefulness, clarity, and source alignment.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_METADATA_COMPLETENESS',
        'Metadata completeness',
        'metadata',
        'major',
        'knowledge_card',
        'threshold',
        'metadata_completeness_pct',
        '>=',
        95,
        '{"required_fields": ["type", "summary", "source_linkage", "scope_or_context"]}'::jsonb,
        8,
        TRUE,
        'Required metadata completeness must be at least 95 percent.',
        'Enforce metadata validation before card acceptance.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_SOURCE_ERROR_RATE',
        'Source error rate',
        'source_quality',
        'blocker',
        'knowledge_card',
        'hard_blocker',
        'source_error_count',
        '=',
        0,
        '{"source": "knowledge_card_reviews"}'::jsonb,
        NULL,
        TRUE,
        'No source error is permitted in qualified knowledge-card templates.',
        'Fix incorrect or broken source associations.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_BROKEN_REFERENCE_RATE',
        'Broken reference rate',
        'source_quality',
        'major',
        'knowledge_card',
        'threshold',
        'broken_reference_rate_pct',
        '<=',
        2,
        '{"source": "knowledge_card_reference_errors"}'::jsonb,
        5,
        TRUE,
        'Broken-reference rate must be 2 percent or lower.',
        'Repair scraping/parsing and revalidate broken links.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_RELEVANCE_ISSUE_RATE',
        'Relevance issue rate',
        'quality',
        'major',
        'knowledge_card',
        'threshold',
        'relevance_issue_rate_pct',
        '<=',
        10,
        '{"source": "knowledge_card_reviews"}'::jsonb,
        5,
        TRUE,
        'Relevance issue rate must be 10 percent or lower.',
        'Improve retrieval and contextual conditioning for card generation.',
        TRUE
    ),
    (
        (SELECT id FROM kc_ruleset),
        'KC_DOWNSTREAM_USABILITY',
        'Downstream proposal usability',
        'business',
        'major',
        'knowledge_card',
        'threshold',
        'downstream_linked_proposal_incident_rate_pct',
        '<=',
        10,
        '{"definition": "share_of_downstream_proposal_incidents_linked_to_this_template"}'::jsonb,
        10,
        TRUE,
        'Knowledge-card templates must not drive downstream proposal incident rates above 10 percent.',
        'Refine the card template if it degrades downstream proposal generation quality.',
        TRUE
    )
) AS seed_rows (
    rule_set_id,
    rule_code,
    rule_name,
    category,
    severity,
    applies_to,
    evaluation_mode,
    metric_name,
    comparator,
    threshold_numeric,
    threshold_json,
    weight,
    required,
    description,
    remediation_guidance,
    is_active
)
ON CONFLICT (rule_set_id, rule_code) DO NOTHING;

-- --------------------------------------------------------------------------
-- 4) REPRESENTATIVE PROPOSAL QUALIFICATION SCENARIOS
-- --------------------------------------------------------------------------
INSERT INTO qualification_scenarios (
    scenario_code,
    template_type,
    name,
    description,
    donor_id,
    outcome_id,
    field_context_id,
    geography,
    metadata,
    active,
    created_by
)
VALUES
(
    'PROPOSAL_STANDARD_SINGLE_DONOR',
    'proposal',
    'Standard single-donor proposal',
    'Baseline proposal scenario for common donor requirements and standard section coverage.',
    NULL,
    NULL,
    NULL,
    '{"scope": "single_country"}'::jsonb,
    '{"archetype": "standard", "risk_profile": "medium", "requires_budget": true}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
),
(
    'PROPOSAL_HIGH_RISK_REGULATED',
    'proposal',
    'High-risk regulated proposal',
    'Validates compliance, security, legal, and financial language in a regulated context.',
    NULL,
    NULL,
    NULL,
    '{"scope": "single_country", "regulatory_context": "high"}'::jsonb,
    '{"archetype": "high_risk", "risk_profile": "high", "critical_sections": ["compliance", "security", "budget"]}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
),
(
    'PROPOSAL_MULTI_CONTEXT_MULTI_COUNTRY',
    'proposal',
    'Multi-context / multi-country proposal',
    'Tests scenario robustness with multiple field contexts and geographic coverage.',
    NULL,
    NULL,
    NULL,
    '{"scope": "multi_country"}'::jsonb,
    '{"archetype": "multi_context", "risk_profile": "medium", "complexity": "high"}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
),
(
    'PROPOSAL_DONOR_STRICT_FORMAT',
    'proposal',
    'Strict donor formatting proposal',
    'Validates strict structural, ordering, and formatting requirements for donor-specific proposals.',
    NULL,
    NULL,
    NULL,
    '{"scope": "single_country"}'::jsonb,
    '{"archetype": "strict_format", "risk_profile": "medium", "format_strictness": "high"}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
)
ON CONFLICT (scenario_code) DO NOTHING;

-- --------------------------------------------------------------------------
-- 5) REPRESENTATIVE KNOWLEDGE-CARD QUALIFICATION SCENARIOS
-- --------------------------------------------------------------------------
INSERT INTO qualification_scenarios (
    scenario_code,
    template_type,
    name,
    description,
    donor_id,
    outcome_id,
    field_context_id,
    geography,
    metadata,
    active,
    created_by
)
VALUES
(
    'KC_DONOR_POLICY_CARD',
    'knowledge_card',
    'Donor policy knowledge card',
    'Validates source traceability, freshness, and policy-oriented factual grounding.',
    NULL,
    NULL,
    NULL,
    '{"scope": "regional"}'::jsonb,
    '{"coverage_group": "donor", "risk_profile": "high", "critical_claims_expected": true}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
),
(
    'KC_OUTCOME_GUIDANCE_CARD',
    'knowledge_card',
    'Outcome guidance knowledge card',
    'Validates outcome-linked guidance cards for relevance and downstream reuse.',
    NULL,
    NULL,
    NULL,
    '{"scope": "global"}'::jsonb,
    '{"coverage_group": "outcome", "risk_profile": "medium", "downstream_use": "proposal_generation"}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
),
(
    'KC_FIELD_CONTEXT_OPERATIONAL_CARD',
    'knowledge_card',
    'Field-context operational card',
    'Validates contextual specificity, metadata completeness, and duplication control.',
    NULL,
    NULL,
    NULL,
    '{"scope": "country"}'::jsonb,
    '{"coverage_group": "field_context", "risk_profile": "medium", "specificity_required": true}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
),
(
    'KC_MULTI_SOURCE_SYNTHESIS_CARD',
    'knowledge_card',
    'Multi-source synthesis card',
    'Tests safe synthesis across multiple linked references and traceability controls.',
    NULL,
    NULL,
    NULL,
    '{"scope": "regional"}'::jsonb,
    '{"coverage_group": "synthesis", "risk_profile": "high", "multi_source": true}'::jsonb,
    TRUE,
    '<ADMIN_USER_ID>'::uuid
)
ON CONFLICT (scenario_code) DO NOTHING;

-- --------------------------------------------------------------------------
-- 6) OPTIONAL EXAMPLE TEMPLATE REGISTRY SEEDS (COMMENTED)
-- --------------------------------------------------------------------------
-- Uncomment and replace values if you want to bootstrap managed templates.
--
INSERT INTO template_registry (
    template_key,
    template_name,
    template_type,
    source_template_request_id,
    owner_user_id,
    owning_team_id,
    description,
    active
) VALUES
(
    'default_proposal_template',
    'Default Proposal Template',
    'proposal',
    NULL,
    '<ADMIN_USER_ID>'::uuid,
    NULL,
    'Baseline proposal template managed under the qualification workflow.',
    TRUE
),
(
    'default_knowledge_card_template',
    'Default Knowledge Card Template',
    'knowledge_card',
    NULL,
    '<ADMIN_USER_ID>'::uuid,
    NULL,
    'Baseline knowledge-card template managed under the qualification workflow.',
    TRUE
)
ON CONFLICT (template_key) DO NOTHING;
--
INSERT INTO template_versions (
    template_registry_id,
    version_label,
    version_number,
    environment,
    status,
    configuration,
    template_content,
    initial_file_content,
    release_notes,
    created_by,
    updated_by
)
SELECT
    tr.id,
    '1.0.0-rc1',
    1,
    'uat',
    'in_uat',
    '{}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    'Initial UAT candidate',
    '<ADMIN_USER_ID>'::uuid,
    '<ADMIN_USER_ID>'::uuid
FROM template_registry tr
WHERE tr.template_key IN ('default_proposal_template', 'default_knowledge_card_template')
ON CONFLICT DO NOTHING;

COMMIT;

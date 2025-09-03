-- Insert a default team
INSERT INTO teams (name) VALUES ('Default Team') ON CONFLICT (name) DO NOTHING;

-- Insert test users
INSERT INTO users (id, email, password, name, team_id) VALUES
(gen_random_uuid(), 'testuser1@example.com', 'scrypt:32768:8:1$DnJpwLdKLgMfnRcu$f58e80a3ca954a73a9e2c7c006e2e909f28ce53863f815e36a7b1294b4c1ceff94c71c226212786b96f380f459fe44d31e72a9d3f5c97846e5c00e98b4e4ff18', 'Test User 1', (SELECT id FROM teams WHERE name = 'Default Team' LIMIT 1)) ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, email, password, name, team_id) VALUES
(gen_random_uuid(), 'testuser2@example.com', 'scrypt:32768:8:1$H7vwtXh7ejJ5EL6Y$b152f7c29f4ed26ef7b4fef693d50de84dc44dcba63ab2130163cbafe04d7c209691abd75a3a5d6c66de62f59a5a686168abda79aac32ff5300216c62ffd4b24', 'Test User 2', (SELECT id FROM teams WHERE name = 'Default Team' LIMIT 1)) ON CONFLICT (email) DO NOTHING;

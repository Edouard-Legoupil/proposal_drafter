-- Add 'proposal writer' role to all existing users
INSERT INTO user_roles (user_id, role_id)
SELECT id, (SELECT id FROM roles WHERE name = 'proposal writer') FROM users
ON CONFLICT (user_id, role_id) DO NOTHING;

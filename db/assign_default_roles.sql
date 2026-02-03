-- SQL Script to assign default roles to users
-- This ensures that all users have at least the 'proposal writer' role,
-- which may be required by the RBAC implementation to prevent disconnections.

-- 1. Ensure the default role exists
INSERT INTO roles (name)
SELECT 'proposal writer'
WHERE NOT EXISTS (
    SELECT 1 FROM roles WHERE name = 'proposal writer'
);

-- 2. Assign the 'proposal writer' role to all users who currently have no roles
-- We use a CROSS JOIN with the specific role to get its ID, and then filter
-- for users who don't already have an entry in the user_roles table.
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN (SELECT id FROM roles WHERE name = 'proposal writer' LIMIT 1) r
WHERE NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
);

-- Optional: Verify the assignment
-- SELECT u.email, r.name as role_name 
-- FROM users u
-- JOIN user_roles ur ON u.id = ur.user_id
-- JOIN roles r ON ur.role_id = r.id;

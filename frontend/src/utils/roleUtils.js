/**
 * Role-based access control utilities for frontend components
 * Enhanced with team leadership, membership status, and object-level access control
 */

/**
 * Check if current user has a specific permission
 * @param {Object} user - User object from context/API
 * @param {string} permission - Permission to check (e.g., 'access_metrics')
 * @returns {boolean} - True if user has permission
 */
export function hasPermission(user, permission) {
  // Admin users have all permissions
  if (user?.is_admin) return true;

  return user?.roles?.includes(permission) || false;
}

/**
 * Check if user has any of the specified permissions
 * @param {Object} user - User object from context/API
 * @param {string[]} permissions - Array of permissions to check
 * @returns {boolean} - True if user has any of the permissions
 */
export function hasAnyPermission(user, permissions) {
  if (user?.is_admin) return true;

  return permissions.some(permission =>
    user?.roles?.includes(permission)
  );
}

/**
 * Check if user is a team leader of any team
 * @param {Object} user - User object from context/API
 * @returns {boolean} - True if user is a team leader
 */
export function isTeamLeader(user) {
  if (user?.is_admin) return true;
  return Boolean(user?.team_leadership && user?.active_team);
}

/**
 * Check if user is a team leader of a specific team
 * @param {Object} user - User object from context/API
 * @param {string} teamId - Team ID to check
 * @returns {boolean} - True if user is a team leader of the specified team
 */
export function isTeamLeaderOf(user, teamId) {
  if (user?.is_admin) return true;
  return Boolean(user?.team_leadership && user?.active_team?.id === teamId);
}

/**
 * Check if user is an active member of a specific team
 * @param {Object} user - User object from context/API
 * @param {string} teamId - Team ID to check
 * @returns {boolean} - True if user is an active member of the team
 */
export function isTeamMember(user, teamId) {
  if (user?.is_admin) return true;
  return user?.active_team?.id === teamId && user?.memberships?.some(
    (membership) => membership.id === teamId && (!membership.status || membership.status === 'ACTIVE')
  ) || false;
}

/**
 * Get user's membership status in a specific team
 * @param {Object} user - User object from context/API
 * @param {string} teamId - Team ID to check
 * @returns {string} - Membership status ('ACTIVE', 'PENDING', 'REJECTED', or 'NOT_MEMBER')
 */
export function getMembershipStatus(user, teamId) {
  if (user?.is_admin) return 'ACTIVE';
  const membership = user?.memberships?.find((item) => item.id === teamId);
  return membership ? (membership.status || 'ACTIVE') : 'NOT_MEMBER';
}

/**
 * Check if user has access to a specific object based on object-level permissions
 * @param {Object} user - User object from context/API
 * @param {Object} objectInfo - Object information (must contain team_id and access_rules)
 * @param {string} requiredPermission - Required permission ('read', 'write', 'delete')
 * @returns {boolean} - True if user has the required permission on the object
 */
export function hasObjectAccess(user, objectInfo, requiredPermission = 'read') {
  if (user?.is_admin) return true;

  // If no object info, deny access
  if (!objectInfo) return false;

  // Access requires an explicit grant for the active team. Ownership is not a bypass.
  if (objectInfo.team_id && isTeamMember(user, objectInfo.team_id)) {
    const teamRule = objectInfo.access_rules?.find(rule => rule.team_id === objectInfo.team_id);
    if (teamRule) {
      const permissions = teamRule.permissions || [];
      const normalizedPermission = requiredPermission === 'write' ? 'edit' : requiredPermission;
      return permissions.includes(normalizedPermission);
    }
  }

  return false;
}

/**
 * Check if user can approve membership requests for a team
 * @param {Object} user - User object from context/API
 * @param {string} teamId - Team ID to check
 * @returns {boolean} - True if user can approve membership requests
 */
export function canApproveMembership(user, teamId) {
  if (user?.is_admin) return true;
  return isTeamLeaderOf(user, teamId);
}

/**
 * Check if user can manage roles for a team
 * @param {Object} user - User object from context/API
 * @param {string} teamId - Team ID to check
 * @returns {boolean} - True if user can manage team roles
 */
export function canManageTeamRoles(user) {
  return Boolean(user?.is_admin);
}

/**
 * Get user's role-based UI configuration
 * @param {Object} user - User object from context/API
 * @returns {Object} - UI visibility configuration
 */
export function getUIConfiguration(user) {
  if (!user) return {
    showMetrics: false,
    showTemplates: false,
    showIncidents: false,
    showQualityGate: false,
    showTeamManagement: false,
    showAdminPanel: false
  };

  return {
    showMetrics: hasPermission(user, 'access_metrics'),
    showTemplates: hasPermission(user, 'access_template'),
    showIncidents: hasPermission(user, 'access_incident'),
    showQualityGate: hasPermission(user, 'access_quality_gate'),
    showTeamManagement: isTeamLeader(user) || user.is_admin,
    showAdminPanel: user.is_admin
  };
}

/**
 * Filter a list of objects based on user's access permissions
 * @param {Object} user - User object from context/API
 * @param {Array} objects - Array of objects to filter
 * @param {string} requiredPermission - Required permission ('read', 'write', 'delete')
 * @returns {Array} - Filtered array of objects user can access
 */
export function filterAccessibleObjects(user, objects, requiredPermission = 'read') {
  if (user?.is_admin) return objects || [];

  if (!objects || !Array.isArray(objects)) return [];

  return objects.filter(obj => hasObjectAccess(user, obj, requiredPermission));
}

/**
 * Get accessible teams for the user
 * @param {Object} user - User object from context/API
 * @returns {Array} - Array of team IDs user can access
 */
export function getAccessibleTeams(user) {
  if (user?.is_admin) return user.all_teams || [];

  // Return teams where user has ACTIVE membership
  return user?.memberships
    ?.filter((membership) => !membership.status || membership.status === 'ACTIVE')
    .map((membership) => membership.id) || [];
}

/**
 * Check if user can create objects for a specific team
 * @param {Object} user - User object from context/API
 * @param {string} teamId - Team ID to check
 * @returns {boolean} - True if user can create objects for the team
 */
export function canCreateForTeam(user, teamId) {
  if (user?.is_admin) return true;

  // User can create for teams they are active members of
  const status = getMembershipStatus(user, teamId);
  return status === 'ACTIVE';
}

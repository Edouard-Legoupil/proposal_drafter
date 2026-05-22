/**
 * Role-based access control utilities for frontend components
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
  
  // Check all roles (including inherited)
  return user?.all_roles?.includes(permission) || false;
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
    user?.all_roles?.includes(permission)
  );
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
    showQualityGate: false
  };
  
  return {
    showMetrics: hasPermission(user, 'access_metrics'),
    showTemplates: hasPermission(user, 'access_template'),
    showIncidents: hasPermission(user, 'access_incident'),
    showQualityGate: hasPermission(user, 'access_quality_gate')
  };
}
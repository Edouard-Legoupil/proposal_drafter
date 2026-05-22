/**
 * Role-based access control utilities for frontend components
 */

/**
 * Check if current user has a specific permission
 * @param {string} permission - Permission to check (e.g., 'access_metrics')
 * @returns {boolean} - True if user has permission
 */
export function hasPermission(permission) {
  // Get user from Redux store or context
  const user = useSelector(state => state.auth.user);
  
  // Admin users have all permissions
  if (user?.is_admin) return true;
  
  // Check all roles (including inherited)
  return user?.all_roles?.includes(permission) || false;
}

/**
 * Check if user has any of the specified permissions
 * @param {string[]} permissions - Array of permissions to check
 * @returns {boolean} - True if user has any of the permissions
 */
export function hasAnyPermission(permissions) {
  const user = useSelector(state => state.auth.user);
  
  if (user?.is_admin) return true;
  
  return permissions.some(permission =>
    user?.all_roles?.includes(permission)
  );
}

/**
 * Get user's role-based UI configuration
 * @returns {Object} - UI visibility configuration
 */
export function getUIConfiguration() {
  const user = useSelector(state => state.auth.user);
  
  if (!user) return {
    showMetrics: false,
    showTemplates: false,
    showIncidents: false,
    showQualityGate: false
  };
  
  return {
    showMetrics: hasPermission('access_metrics'),
    showTemplates: hasPermission('access_template'),
    showIncidents: hasPermission('access_incident'),
    showQualityGate: hasPermission('access_quality_gate')
  };
}
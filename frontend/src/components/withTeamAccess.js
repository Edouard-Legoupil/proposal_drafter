import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { hasPermission, isTeamLeaderOf, isTeamMember } from '../utils/roleUtils';
import { CircularProgress, Box, Alert } from '@mui/material';

/**
 * Higher-Order Component for team-based access control
 * Wraps components to enforce team membership and role requirements
 *
 * @param {Object} options - Access control options
 * @param {string} options.teamId - Required team ID
 * @param {string|string[]} [options.requiredPermission] - Required permission(s)
 * @param {boolean} [options.requireTeamLeader] - Require team leader status
 * @param {React.Component} WrappedComponent - Component to wrap
 * @returns {React.Component} - Wrapped component with access control
 */
export function withTeamAccess(options) {
  return function (WrappedComponent) {
    return function WithTeamAccess(props) {
      const { user, isLoading: authLoading } = useAuth();
      const navigate = useNavigate();

      // If still loading auth state, show loading indicator
      if (authLoading) {
        return (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        );
      }

      // If no user, redirect to login
      if (!user) {
        navigate('/login', { replace: true });
        return null;
      }

      // Admin users have access to everything
      if (user.is_admin) {
        return <WrappedComponent {...props} />;
      }

      // Check team membership if teamId is specified
      if (options.teamId) {
        const isMember = isTeamMember(user, options.teamId);

        // If not a member, show access denied
        if (!isMember) {
          return (
            <Box sx={{ p: 3 }}>
              <Alert severity="error">
                You must be a member of this team to access this content.
              </Alert>
            </Box>
          );
        }

        // Check team leader requirement
        if (options.requireTeamLeader) {
          const isLeader = isTeamLeaderOf(user, options.teamId);

          if (!isLeader) {
            return (
              <Box sx={{ p: 3 }}>
                <Alert severity="error">
                  You must be a team leader to access this content.
                </Alert>
              </Box>
            );
          }
        }

        // Check required permissions
        if (options.requiredPermission) {
          const permissions = Array.isArray(options.requiredPermission)
            ? options.requiredPermission
            : [options.requiredPermission];

          const hasRequiredPermission = permissions.some(perm =>
            hasPermission(user, perm)
          );

          if (!hasRequiredPermission) {
            return (
              <Box sx={{ p: 3 }}>
                <Alert severity="error">
                  You don't have the required permissions to access this content.
                </Alert>
              </Box>
            );
          }
        }
      }

      // If all checks pass, render the component
      return <WrappedComponent {...props} />;
    };
  };
}

/**
 * Convenience wrapper for team member access
 * @param {string} teamId - Required team ID
 * @param {React.Component} WrappedComponent - Component to wrap
 */
export function requireTeamMember(teamId) {
  return withTeamAccess({ teamId });
}

/**
 * Convenience wrapper for team leader access
 * @param {string} teamId - Required team ID
 * @param {React.Component} WrappedComponent - Component to wrap
 */
export function requireTeamLeader(teamId) {
  return withTeamAccess({ teamId, requireTeamLeader: true });
}

/**
 * Convenience wrapper for permission-based access
 * @param {string|string[]} requiredPermission - Required permission(s)
 * @param {React.Component} WrappedComponent - Component to wrap
 */
export function requirePermission(requiredPermission) {
  return withTeamAccess({ requiredPermission });
}

/**
 * Convenience wrapper for team member with specific permission
 * @param {string} teamId - Required team ID
 * @param {string|string[]} requiredPermission - Required permission(s)
 * @param {React.Component} WrappedComponent - Component to wrap
 */
export function requireTeamMemberWithPermission(teamId, requiredPermission) {
  return withTeamAccess({ teamId, requiredPermission });
}

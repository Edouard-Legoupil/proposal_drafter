import { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../utils/api';

/**
 * Custom hook for team membership operations
 * Provides functions for joining teams, approving/rejecting requests, and managing team roles
 */
export function useTeamMembership() {
  const { user, updateUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Request to join a team
   * @param {string} teamId - ID of the team to join
   * @returns {Promise<boolean>} - True if request was successful
   */
  const requestTeamMembership = useCallback(async (teamId) => {
    if (!user) {
      setError('User not authenticated');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post(`/teams/${teamId}/join`);

      // Update user's team membership status
      if (updateUser) {
        updateUser({
          ...user,
          team_membership_status: {
            ...user.team_membership_status,
            [teamId]: 'PENDING'
          }
        });
      }

      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to request team membership');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user, updateUser]);

  /**
   * Get pending membership requests for a team
   * @param {string} teamId - ID of the team
   * @returns {Promise<Array>} - Array of pending requests
   */
  const getPendingRequests = useCallback(async (teamId) => {
    if (!user) {
      setError('User not authenticated');
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get(`/teams/${teamId}/requests`);
      return response.data.pending_requests || [];
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch pending requests');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Approve a team membership request
   * @param {string} teamId - ID of the team
   * @param {string} userId - ID of the user to approve
   * @returns {Promise<boolean>} - True if approval was successful
   */
  const approveMembership = useCallback(async (teamId, userId) => {
    if (!user) {
      setError('User not authenticated');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post(`/teams/${teamId}/approve/${userId}`);
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve membership');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Reject a team membership request
   * @param {string} teamId - ID of the team
   * @param {string} userId - ID of the user to reject
   * @returns {Promise<boolean>} - True if rejection was successful
   */
  const rejectMembership = useCallback(async (teamId, userId) => {
    if (!user) {
      setError('User not authenticated');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post(`/teams/${teamId}/reject/${userId}`);
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reject membership');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Get roles assigned to a team
   * @param {string} teamId - ID of the team
   * @returns {Promise<Array>} - Array of team roles
   */
  const getTeamRoles = useCallback(async (teamId) => {
    if (!user) {
      setError('User not authenticated');
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get(`/teams/${teamId}/roles`);
      return response.data.roles || [];
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch team roles');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Assign a role to a team (admin only)
   * @param {string} teamId - ID of the team
   * @param {number} roleId - ID of the role to assign
   * @returns {Promise<boolean>} - True if assignment was successful
   */
  const assignRoleToTeam = useCallback(async (teamId, roleId) => {
    if (!user?.is_admin) {
      setError('Only administrators can assign roles to teams');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post(`/teams/${teamId}/roles`, { role_id: roleId });
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assign role to team');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Remove a role from a team (admin only)
   * @param {string} teamId - ID of the team
   * @param {number} roleId - ID of the role to remove
   * @returns {Promise<boolean>} - True if removal was successful
   */
  const removeRoleFromTeam = useCallback(async (teamId, roleId) => {
    if (!user?.is_admin) {
      setError('Only administrators can remove roles from teams');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.delete(`/teams/${teamId}/roles/${roleId}`);
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove role from team');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Check if current user can approve membership requests for a team
   * @param {string} teamId - ID of the team
   * @returns {boolean} - True if user can approve requests
   */
  const canApproveMembership = useCallback((teamId) => {
    if (!user) return false;
    if (user.is_admin) return true;

    // Check if user is team leader of this team
    return user.team_leadership?.includes(teamId) || false;
  }, [user]);

  /**
   * Check if current user can manage roles for a team
   * @param {string} teamId - ID of the team
   * @returns {boolean} - True if user can manage team roles
   */
  const canManageTeamRoles = useCallback((teamId) => {
    if (!user) return false;
    if (user.is_admin) return true;

    // Check if user is team leader of this team
    return user.team_leadership?.includes(teamId) || false;
  }, [user]);

  return {
    isLoading,
    error,
    requestTeamMembership,
    getPendingRequests,
    approveMembership,
    rejectMembership,
    getTeamRoles,
    assignRoleToTeam,
    removeRoleFromTeam,
    canApproveMembership,
    canManageTeamRoles
  };
}

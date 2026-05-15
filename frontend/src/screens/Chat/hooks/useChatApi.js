/**
 * Custom hook for API calls in the Chat component
 *
 * Handles data fetching for donors, outcomes, field contexts, geographic coverages, users, etc.
 */

import { useState, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

/**
 * Custom hook for chat-related API calls
 * @param {Object} initialData - Optional initial data
 * @returns {Object} API state and functions
 */

export const useChatApi = () => {
	const [donors, setDonors] = useState([{ id: '1', name: 'USAID' }]);
	const [outcomes, setOutcomes] = useState([{ id: '1', name: 'OA1-Access/Documentation' }]);
	const [fieldContexts, setFieldContexts] = useState([{ id: '1', name: 'USA', geographic_coverage: 'One Country Operation' }]);
	const [filteredFieldContexts, setFilteredFieldContexts] = useState([{ id: '1', name: 'USA', geographic_coverage: 'One Country Operation' }]);
	const [newBudgetRanges, setNewBudgetRanges] = useState([]);
	const [newDurations, setNewDurations] = useState([]);
	const [geographicCoverages, setGeographicCoverages] = useState(['One Country Operation']);
  const [users, setUsers] = useState([]);
  const [transferUsers, setTransferUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [isReviewer, setIsReviewer] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  /**
   * Fetches initial form data (donors, outcomes, field contexts, geographic coverages)
   */
  const fetchData = useCallback(async () => {
    try {
      const [donorsRes, outcomesRes, fieldContextsRes, geoCoveragesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
        fetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
        fetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' }),
        fetch(`${API_BASE_URL}/geographic-coverages`, { credentials: 'include' })
      ]);

      if (donorsRes.ok) {
        const data = await donorsRes.json();
        setDonors(data.donors);
      }
      if (outcomesRes.ok) {
        const data = await outcomesRes.json();
        setOutcomes(data.outcomes);
      }
      if (fieldContextsRes.ok) {
        const data = await fieldContextsRes.json();
        const sortedFieldContexts = data.field_contexts.sort((a, b) => a.name.localeCompare(b.name));
        setFieldContexts(sortedFieldContexts);
        setFilteredFieldContexts(sortedFieldContexts);
      }
      if (geoCoveragesRes.ok) {
        const data = await geoCoveragesRes.json();
        setGeographicCoverages(data.geographic_coverages || []);
      }
    } catch (error) {
      console.error("Error fetching form data:", error);
    }
  }, []);

  /**
   * Fetches all users
   */
  const getUsers = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      // Handle both flat list and dictionary structure
      const userList = Array.isArray(data) ? data : (data.users || []);
      const formattedUsers = userList.map(user => ({
        id: user.id,
        name: user.name,
        team: user.team_name || 'Unassigned',
        donor_ids: user.donor_ids || [],
        outcomes: user.outcomes || [],
        field_contexts: user.field_contexts || []
      }));
      setUsers(formattedUsers.sort((a, b) => a.name.localeCompare(b.name)));
    }
  }, []);

  /**
   * Fetches users eligible for proposal transfer
   */
  const getTransferUsers = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/users?role=proposal%20drafter`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      const userList = Array.isArray(data) ? data : (data.users || []);
      setTransferUsers(userList.map(user => ({
        id: user.id,
        name: user.name,
        team: user.team_name || 'Unassigned'
      })));
    } else {
      console.error("Failed to fetch transfer users", response.status);
    }
  }, []);

  /**
   * Fetches the current user profile
   */
  const getProfile = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile`, { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data);
        setIsReviewer(data.role === 'reviewer' || false);
        setIsAdmin(data.role === 'admin' || false);
      }
    } catch (error) {
      console.error("Error fetching profile:", error);
    }
  }, []);

  /**
   * Filters field contexts based on geographical scope
   * @param {string} scope - The geographical scope value
   */
  const updateFilteredFieldContexts = useCallback((scope) => {
    const filtered = scope
      ? fieldContexts.filter(fc => fc.geographic_coverage === scope)
      : fieldContexts;
    setFilteredFieldContexts(filtered);
  }, [fieldContexts]);

  return {
    // State
    donors,
    outcomes,
    fieldContexts,
    filteredFieldContexts,
    newBudgetRanges,
    newDurations,
    geographicCoverages,
    users,
    transferUsers,
    currentUser,
    isReviewer,
    isAdmin,
    // Setters
    setDonors,
    setOutcomes,
    setFieldContexts,
    setFilteredFieldContexts,
    setNewBudgetRanges,
    setNewDurations,
    setGeographicCoverages,
    setUsers,
    setTransferUsers,
    setCurrentUser,
    setIsReviewer,
    setIsAdmin,
    // Functions
    fetchData,
    getUsers,
    getTransferUsers,
    getProfile,
    updateFilteredFieldContexts
  };
};

export default useChatApi;

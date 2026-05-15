/**
 * Custom hook for managing proposal state and logic in the Chat component
 *
 * Handles proposal data, generation, editing, and related state.
 */

import { useState, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

/**
 * Custom hook for proposal management
 * @param {Object} options - Optional parameters
 * @param {Function} options.setCurrentUser - Setter for currentUser from useChatApi
 * @param {Function} options.setIsAdmin - Setter for isAdmin from useChatApi
 * @param {Function} options.setIsReviewer - Setter for isReviewer from useChatApi
 * @returns {Object} Proposal state and handlers
 */
export const useProposal = ({ setCurrentUser, setIsAdmin, setIsReviewer } = {}) => {
  const navigate = useNavigate();
  const { id } = useParams();

  // Proposal state
  const [proposal, setProposal] = useState({});
  const [proposalTemplate, setProposalTemplate] = useState(null);
  const [proposalStatus, setProposalStatus] = useState("draft");
  const [generateLoading, setGenerateLoading] = useState(false);
  const [generateLabel, setGenerateLabel] = useState("Generate");
  const [contributionId, setContributionId] = useState("");
  const [statusHistory, setStatusHistory] = useState([]);

  // Section editing state
  const [isEdit, setIsEdit] = useState(false);
  const [editorContent, setEditorContent] = useState("");
  const [selectedSectionName, setSelectedSectionName] = useState(null);
  const [isCopied, setIsCopied] = useState(false);
  const copyResetTimerRef = useRef(null);

  // Generation state
  const isGenerating = useRef(false);
  const fromFollowUpModalRef = useRef(false);

  // Refs
  const topRef = useRef();
  const proposalRef = useRef();

  // Associated knowledge cards
  const [associatedKnowledgeCards, setAssociatedKnowledgeCards] = useState([]);

  // Reviews
  const [reviews, setReviews] = useState([]);
  const [reviewComments, setReviewComments] = useState({});
  const [reviewStatus, setReviewStatus] = useState({});

  /**
   * Handles copy click for section content
   */
  const handleCopyClick = useCallback(async (sectionName, content) => {
    try {
      await navigator.clipboard.writeText(content);
      setIsCopied(true);

      if (copyResetTimerRef.current) {
        clearTimeout(copyResetTimerRef.current);
      }

      copyResetTimerRef.current = setTimeout(() => {
        setIsCopied(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to copy section content:', error);
      // setNotif can be called from parent component
    }
  }, []);

  /**
   * Handles section expander toggle
   */
  const handleExpanderToggle = useCallback((sectionName) => {
    setProposal(p => ({
      ...p,
      [sectionName]: {
        content: p[sectionName].content,
        open: !p[sectionName].open
      }
    }));
  }, []);

  /**
   * Handles edit/save click for a section
   */
  const handleEditClick = useCallback(async (sectionName) => {
    if (!isEdit) {
      // Entering edit mode
      setSelectedSectionName(sectionName);
      setIsEdit(true);
      setEditorContent(proposal[sectionName]?.content || "");
    } else {
      // Saving changes
      try {
        const response = await fetch(`${API_BASE_URL}/update_section/${sessionStorage.getItem("proposal_id")}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            section: selectedSectionName,
            content: editorContent
          }),
          credentials: 'include'
        });

        if (response.ok) {
          setProposal(p => ({
            ...p,
            [selectedSectionName]: {
              ...p[selectedSectionName],
              content: editorContent,
              open: true
            }
          }));
          setIsEdit(false);
          setEditorContent("");
          setSelectedSectionName(null);
        }
      } catch (error) {
        console.error("Error saving section:", error);
      }
    }
  }, [isEdit, editorContent, proposal, selectedSectionName]);

  /**
   * Handles section regeneration
   */
  const handleRegenerateIconClick = useCallback((sectionName) => {
    setSelectedSectionName(sectionName);
    // setIsRegenerateModalOpen can be called from parent
  }, []);

  /**
   * Handles comment change for a section
   */
  const handleCommentChange = useCallback(async (section, field, value) => {
    setReviewComments(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  }, []);

  /**
   * Handles status change for a review
   */
  const handleStatusChange = useCallback((section, status) => {
    setReviewStatus(prev => ({
      ...prev,
      [section]: status
    }));
  }, []);

  /**
   * Handles comment deletion
   */
  const handleDeleteComment = useCallback(async () => {
    // Implementation can be added here
  }, []);

  /**
   * Handles reply to feedback
   */
  const handleReplyToFeedback = useCallback(async () => {
    // Implementation can be added here
  }, []);

  /**
   * Handles saving a response
   */
  const handleSaveResponse = useCallback(async () => {
    // Implementation can be added here
  }, []);

  /**
   * Handles section click in sidebar
   */
  const handleSidebarSectionClick = useCallback((sectionIndex) => {
    setSelectedSectionName(null);
    setIsEdit(false);

    if (sectionIndex === -1 && topRef?.current) {
      topRef?.current?.scroll({ top: 0, behavior: "smooth" });
    } else if (proposalRef.current) {
      proposalRef?.current?.children[sectionIndex]?.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  /**
   * Fetches proposal content from backend
   */
  const getContent = useCallback(async () => {
    if (sessionStorage.getItem("proposal_id")) {
      const response = await fetch(`${API_BASE_URL}/load-draft/${sessionStorage.getItem("proposal_id")}`, {
        method: "GET",
        headers: { 'Content-Type': 'application/json' },
        credentials: "include"
      });

      if (response.ok) {
        const data = await response.json();

        // Ownership check
        const profileRes = await fetch(`${API_BASE_URL}/profile`, { credentials: 'include' });
        if (profileRes.ok) {
          const profileData = await profileRes.json();
          const curUser = profileData.user;
          setCurrentUser(curUser);
          const ownerId = data.user_id;
          const isOwner = curUser.id === ownerId || curUser.user_id === ownerId;
          const _isAdmin = curUser.is_admin || (curUser.roles || []).some(r => r === 'admin' || (r && r.name === 'admin'));
          setIsAdmin(_isAdmin);

          if (!isOwner) {
            setIsReviewer(true);
          }
        }

        sessionStorage.setItem("proposal_id", data.proposal_id);
        sessionStorage.setItem("session_id", data.session_id);

        // This would need to be called from the parent component
        // setUserPrompt(data.project_description);
        // setFormData(...);
        // etc.

        const sectionState = {};
        Object.entries(data.generated_sections || {}).forEach(([key, value]) => {
          sectionState[key] = {
            content: value,
            open: true
          };
        });
        setProposal(sectionState);

        if (data.associated_knowledge_cards) {
          setAssociatedKnowledgeCards(data.associated_knowledge_cards);
        }

        if (data.template_name && data.template_name.startsWith("concept_note_")) {
          // setDocumentType("concept note"); // Would need to be passed in
        } else {
          // setDocumentType("proposal");
        }

        setProposalStatus(data.status);
        setContributionId(data.contribution_id || "");
        // setSidebarOpen(true); // Would need to be passed in
        // getStatusHistory();
        // getPeerReviews();

        const storedTemplate = sessionStorage.getItem("proposal_template");
        if (storedTemplate) {
          setProposalTemplate(JSON.parse(storedTemplate));
        }
      } else if (response.status === 401) {
        sessionStorage.setItem("session_expired", "Session expired. Please login again.");
        navigate("/login");
      }
    }
  }, [navigate, setCurrentUser, setIsAdmin, setIsReviewer, setProposal, setAssociatedKnowledgeCards, setProposalStatus, setContributionId, setProposalTemplate]);

  /**
   * Fetches peer reviews for the current proposal
   */
  const getPeerReviews = useCallback(async () => {
    if (sessionStorage.getItem("proposal_id")) {
      const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/peer-reviews`, {
        method: "GET",
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setReviews(data.reviews);
      } else if (response.status === 403) {
        setReviews([]);
      }
    }
  }, [setReviews]);

  /**
   * Fetches status history for the proposal
   */
  const getStatusHistory = useCallback(async () => {
    // Implementation can be added here
    const history = [];
    setStatusHistory(history);
  }, [setStatusHistory]);

  /**
   * Saves contribution ID
   */
  const handleSaveContributionId = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/proposals/${sessionStorage.getItem("proposal_id")}/save-contribution-id`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contribution_id: contributionId }),
      credentials: 'include'
    });

    if (response.ok) {
      alert("Contribution ID saved!");
    } else {
      console.error("Failed to save Contribution ID");
      alert("Failed to save Contribution ID.");
    }
  }, [contributionId]);

  return {
    // Proposal state
    proposal,
    setProposal,
    proposalTemplate,
    setProposalTemplate,
    proposalStatus,
    setProposalStatus,
    generateLoading,
    setGenerateLoading,
    generateLabel,
    setGenerateLabel,
    contributionId,
    setContributionId,
    statusHistory,
    setStatusHistory,

    // Editing state
    isEdit,
    setIsEdit,
    editorContent,
    setEditorContent,
    selectedSectionName,
    setSelectedSectionName,
    isCopied,
    setIsCopied,

    // Generation state
    isGenerating,
    fromFollowUpModalRef,

    // Refs
    topRef,
    proposalRef,

    // Associated knowledge
    associatedKnowledgeCards,
    setAssociatedKnowledgeCards,

    // Reviews
    reviews,
    setReviews,
    reviewComments,
    setReviewComments,
    reviewStatus,
    setReviewStatus,

    // Nav
    navigate,
    id,

    // Handlers
    handleCopyClick,
    handleExpanderToggle,
    handleEditClick,
    handleRegenerateIconClick,
    handleCommentChange,
    handleStatusChange,
    handleDeleteComment,
    handleReplyToFeedback,
    handleSaveResponse,
    handleSidebarSectionClick,

    // New handlers
    getContent,
    getPeerReviews,
    getStatusHistory,
    handleSaveContributionId
  };
};

export default useProposal;

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
 * @returns {Object} Proposal state and handlers
 */
export const useProposal = () => {
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
  const handleDeleteComment = useCallback(async (commentOrSection) => {
    // Implementation can be added here
  }, []);

  /**
   * Handles reply to feedback
   */
  const handleReplyToFeedback = useCallback(async (feedbackId, replyText, replyStatus) => {
    // Implementation can be added here
  }, []);

  /**
   * Handles saving a response
   */
  const handleSaveResponse = useCallback(async (section, responseText) => {
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
    handleSidebarSectionClick
  };
};

export default useProposal;

/**
 * Custom hook for managing modal state in the Chat component
 *
 * Centralizes all modal-related state and handlers.
 */

import { useState } from 'react';

/**
 * Custom hook for modal state management
 * @returns {Object} Modal state and setters
 */
export const useModalState = () => {
  // Navigation and UI state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Modal states
  const [isPeerReviewModalOpen, setIsPeerReviewModalOpen] = useState(false);
  const [isAssociateKnowledgeModalOpen, setIsAssociateKnowledgeModalOpen] = useState(false);
  const [isPdfUploadModalOpen, setIsPdfUploadModalOpen] = useState(false);
  const [isValidationModalOpen, setIsValidationModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [showFollowUpModal, setShowFollowUpModal] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [isRegenerateModalOpen, setIsRegenerateModalOpen] = useState(false);

  // Form state for modals
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [validationMissingFields, setValidationMissingFields] = useState([]);
  const [followUpInstruction, setFollowUpInstruction] = useState("");
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationMessage, setGenerationMessage] = useState("");
  const [regenerateInput, setRegenerateInput] = useState("");
  const [regenerateSectionLoading, setRegenerateSectionLoading] = useState(false);

  // Notification state
  const [notif, setNotif] = useState({ open: false, message: '', severity: 'info' });

  // Resize handler
  const handleResize = () => {
    setIsMobile(window.innerWidth < 768);
  };

  return {
    // Navigation and UI
    sidebarOpen,
    setSidebarOpen,
    isMobile,
    setIsMobile,
    isMobileMenuOpen,
    setIsMobileMenuOpen,

    // Modal visibility
    isPeerReviewModalOpen,
    setIsPeerReviewModalOpen,
    isAssociateKnowledgeModalOpen,
    setIsAssociateKnowledgeModalOpen,
    isPdfUploadModalOpen,
    setIsPdfUploadModalOpen,
    isValidationModalOpen,
    setIsValidationModalOpen,
    isTransferModalOpen,
    setIsTransferModalOpen,
    showFollowUpModal,
    setShowFollowUpModal,
    isProgressModalOpen,
    setIsProgressModalOpen,
    isRegenerateModalOpen,
    setIsRegenerateModalOpen,

    // Form state for modals
    selectedUsers,
    setSelectedUsers,
    validationMissingFields,
    setValidationMissingFields,
    followUpInstruction,
    setFollowUpInstruction,
    generationProgress,
    setGenerationProgress,
    generationMessage,
    setGenerationMessage,
    regenerateInput,
    setRegenerateInput,
    regenerateSectionLoading,
    setRegenerateSectionLoading,

    // Notification
    notif,
    setNotif,

    // Handlers
    handleResize
  };
};

export default useModalState;

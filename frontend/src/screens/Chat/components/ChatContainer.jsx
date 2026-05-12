/**
 * ChatContainer Component
 * 
 * Main container that orchestrates all Chat sub-components using custom hooks.
 * This component will eventually replace the main Chat.jsx component.
 */

import React, { useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Snackbar, Alert } from '@mui/material';

// Custom hooks
import { useFormData, toKebabCase } from '../hooks/useFormData';
import { useChatApi } from '../hooks/useChatApi';
import { useModalState } from '../hooks/useModalState';
import { useProposal } from '../hooks/useProposal';

// Components
import Base from '../../../components/Base/Base';
import CommonButton from '../../../components/CommonButton/CommonButton';
import MultiSelectModal from '../../../components/MultiSelectModal/MultiSelectModal';
import AssociateKnowledgeModal from '../../../components/AssociateKnowledgeModal/AssociateKnowledgeModal';
import PdfUploadModal from '../../../components/PdfUploadModal/PdfUploadModal';
import SingleSelectUserModal from '../../../components/SingleSelectUserModal/SingleSelectUserModal';
import SectionReview from '../../../components/SectionReview/SectionReview';

// Local components
import { FollowUpModal, ValidationModal, ProgressModal, RegenerateModal, Sidebar, Header, ProposalContainer } from './index';

// Assets
import fileIcon from "../../../assets/images/chat-titleIcon.svg";
import generateIcon from "../../../assets/images/generateIcon.svg";
import knowIcon from "../../../assets/images/knowIcon.svg";
import resultsIcon from "../../../assets/images/Chat_resultsIcon.svg";
import edit from "../../../assets/images/Chat_edit.svg";
import save from "../../../assets/images/Chat_save.svg";
import cancel from "../../../assets/images/Chat_editCancel.svg";
import copy from "../../../assets/images/Chat_copy.svg";
import tick from "../../../assets/images/Chat_copiedTick.svg";
import regenerate from "../../../assets/images/Chat_regenerate.svg";
import regenerateClose from "../../../assets/images/Chat_regenerateClose.svg";
import word_icon from "../../../assets/images/word.svg";
import excel_icon from "../../../assets/images/excel.svg";

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

const ChatContainer = (props) => {
  // Initialize all custom hooks
  const { 
    formData, 
    setFormData, 
    formExpanded, 
    setFormExpanded,
    handleFormInput,
    getMissingFields,
    getOptions,
    handleCreate,
    renderFormField
  } = useFormData();

  const { 
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
    setFilteredFieldContexts,
    fetchData,
    getUsers,
    getTransferUsers,
    getProfile
  } = useChatApi();

  const {
    sidebarOpen,
    setSidebarOpen,
    isMobile,
    setIsMobile,
    isMobileMenuOpen,
    setIsMobileMenuOpen,
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
    notif,
    setNotif,
    handleResize
  } = useModalState();

  const {
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
    isEdit,
    setIsEdit,
    editorContent,
    setEditorContent,
    selectedSectionName,
    setSelectedSectionName,
    isCopied,
    setIsCopied,
    fromFollowUpModalRef,
    topRef,
    proposalRef,
    associatedKnowledgeCards,
    setAssociatedKnowledgeCards,
    reviews,
    setReviews,
    reviewComments,
    setReviewComments,
    reviewStatus,
    setReviewStatus,
    navigate,
    id,
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
  } = useProposal();

  // Local state
  const [documentType, setDocumentType] = React.useState("proposal");
  const [titleName, setTitleName] = React.useState(props?.title ?? "Generate Draft Proposal");
  const [userPrompt, setUserPrompt] = React.useState("");
  const [buttonEnable, setButtonEnable] = React.useState(false);

  // Initialize
  useEffect(() => {
    if (id) {
      sessionStorage.setItem("proposal_id", id);
    }
    fetchData().then(() => {
      if (sessionStorage.getItem("proposal_id")) {
        getContent();
      }
    });
    getUsers();
    getTransferUsers();
    getProfile();
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [id]);

  // Update button enable state
  useEffect(() => {
    const existingProposalId = sessionStorage.getItem("proposal_id");
    if (existingProposalId) {
      setButtonEnable(true);
    } else {
      const missing = getMissingFields(userPrompt, formData);
      setButtonEnable(missing.length === 0);
    }
  }, [userPrompt, formData, getMissingFields]);

  // Set label based on existing proposal
  useEffect(() => {
    if (sessionStorage.getItem("proposal_id")) {
      setGenerateLabel("Regenerate");
    }
  }, []);

  // Update title based on document type
  useEffect(() => {
    if (!titleName === "Generate Draft Proposal" || titleName === "Generate Concept Note") {
      if (documentType === "concept note") {
        setTitleName("Generate Concept Note");
      } else {
        setTitleName("Generate Draft Proposal");
      }
    }
  }, [documentType]);

  // Scroll to top after generation
  useEffect(() => {
    if (!generateLoading && proposal && Object.values(proposal).every(section => section.content)) {
      topRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [generateLoading, proposal]);

  // Auto-associate knowledge cards when peer review modal opens
  useEffect(() => {
    if (isPeerReviewModalOpen && users.length > 0) {
      const proposalDonors = Array.isArray(formData["Targeted Donor"]?.value) 
        ? formData["Targeted Donor"].value 
        : (formData["Targeted Donor"]?.value ? [formData["Targeted Donor"].value] : []);
      const proposalOutcomes = formData["Main Outcome"]?.value || [];
      const proposalFieldContexts = Array.isArray(formData["Country / Location(s)"]?.value)
        ? formData["Country / Location(s)"]?.value
        : (formData["Country / Location(s)"]?.value ? [formData["Country / Location(s)"]?.value] : []);

      const matchedUsers = users.filter(user => {
        const donorMatch = (user.donor_ids || []).some(id => proposalDonors.includes(id));
        const outcomeMatch = (user.outcomes || []).some(id => proposalOutcomes.includes(id));
        const contextMatch = (user.field_contexts || []).some(id => proposalFieldContexts.includes(id));
        return donorMatch || outcomeMatch || contextMatch;
      });

      if (matchedUsers.length > 0) {
        setSelectedUsers(matchedUsers);
      }
    }
  }, [isPeerReviewModalOpen, users, formData]);

  // Filter field contexts based on geographical scope
  useEffect(() => {
    const scope = formData['Geographical Scope']?.value;
    const filtered = scope
      ? fieldContexts.filter(fc => fc.geographic_coverage === scope)
      : fieldContexts;
    setFilteredFieldContexts(filtered);

    const locationValue = formData['Country / Location(s)']?.value;
    if (locationValue) {
      if (Array.isArray(locationValue)) {
        const validLocations = locationValue.filter(id => filtered.some(fc => fc.id === id));
        if (validLocations.length !== locationValue.length) {
          handleFormInput({ target: { value: validLocations } }, "Country / Location(s)");
        }
      } else {
        const isLocationStillValid = filtered.some(fc => fc.id === locationValue);
        if (fieldContexts.length > 0 && !isLocationStillValid) {
          handleFormInput({ target: { value: "" } }, "Country / Location(s)");
        }
      }
    }
  }, [formData['Geographical Scope']?.value, fieldContexts, handleFormInput]);

  // Polling logic for proposal generation
  useEffect(() => {
    if (!generateLoading) return;

    setNotif({ open: true, message: 'Generating proposal…', severity: 'info' });
    setGenerationProgress(0);
    setGenerationMessage("Starting proposal generation...");
    setIsProgressModalOpen(true);

    let pollingActive = true;
    const pollInterval = setInterval(async () => {
      if (!pollingActive) return;
      const proposalId = sessionStorage.getItem("proposal_id");
      if (!proposalId) return;

      try {
        const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/status`, { credentials: 'include' });
        if (response.ok) {
          const data = await response.json();
          if (data.generated_sections) {
            let total = Object.keys(data.generated_sections).length;
            if (data.expected_sections && data.expected_sections > 0) {
              setGenerationProgress(Math.round(100 * total / data.expected_sections));
            } else {
              setGenerationProgress(10 + Math.min(85, total * 15));
            }

            const lastSection = Object.keys(data.generated_sections).pop();
            if (lastSection) {
              setGenerationMessage(`Generating section: ${lastSection}...`);
            }

            const sectionState = {};
            Object.entries(data.generated_sections).forEach(([key, value]) => {
              sectionState[key] = {
                content: value,
                open: true
              };
            });
            setProposal(sectionState);

            const generatedCount = Object.keys(data.generated_sections || {}).length;
            const hasAllSections = data.expected_sections > 0
              ? generatedCount >= data.expected_sections
              : generatedCount > 0;
            const isFailed = data.status === 'failed';

            if ((data.status !== 'generating_sections' && hasAllSections) || isFailed) {
              setGenerateLoading(false);
              setGenerationProgress(100);
              setGenerationMessage(isFailed ? "Generation failed!" : "Generation completed!");
              setNotif({ open: true, message: isFailed ? 'Proposal generation failed!' : 'Proposal generation completed!', severity: isFailed ? 'error' : 'success' });
              pollingActive = false;
              clearInterval(pollInterval);
              setTimeout(() => setIsProgressModalOpen(false), 1000);

              if (!isFailed && hasAllSections) {
                setGenerateLabel("Regenerate");
              }
            }
          }
        }
      } catch (err) {
        setGenerateLoading(false);
        setGenerationProgress(0);
        setNotif({ open: true, message: 'Error streaming proposal content. Try again.', severity: 'error' });
        setIsProgressModalOpen(false);
        pollingActive = false;
        clearInterval(pollInterval);
      }
    }, 1000);
    return () => { pollingActive = false; clearInterval(pollInterval); };
  }, [generateLoading]);

  // Functions that need to be defined (will be moved to hooks later)
  const getContent = async () => {};
  const handleGenerateClick = async () => {};
  const handleRegenerateWithFollowUp = async () => {};
  const handleRegenerateButtonClick = async () => {};
  const fetchAndAssociateKnowledgeCards = async () => {};
  const handleSubmitForPeerReview = async () => {};
  const confirmTransfer = async () => {};
  const handleSetStatus = async () => {};
  const handleRevert = async () => {};
  const handleSubmit = async () => {};
  const handleSaveContributionId = async () => {};
  const handlePdfUpload = async () => {};
  const handleExport = async () => {};
  const handleExportTables = async () => {};

  return (
    <Base>
      <div className={`Chat ${isMobile && isMobileMenuOpen ? 'mobile-menu-open' : ''}`} data-testid="chat-container">
        <Snackbar
          open={notif.open}
          autoHideDuration={notif.severity === "info" ? 1400 : 5000}
          onClose={() => setNotif(v => ({ ...v, open: false }))}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity={notif.severity} onClose={() => setNotif(v => ({ ...v, open: false }))} sx={{ width: '100%' }}>
            {notif.message}
          </Alert>
        </Snackbar>

        <ProgressModal
          isOpen={isProgressModalOpen}
          onClose={() => setIsProgressModalOpen(false)}
          progress={generationProgress}
          message={generationMessage}
        />

        <MultiSelectModal
          isOpen={isPeerReviewModalOpen}
          onClose={() => setIsPeerReviewModalOpen(false)}
          options={users}
          selectedOptions={selectedUsers}
          onSelectionChange={setSelectedUsers}
          onConfirm={handleSubmitForPeerReview}
          title="Select Users for Peer Review"
          showDeadline={true}
        />

        <SingleSelectUserModal
          isOpen={isTransferModalOpen}
          onClose={() => setIsTransferModalOpen(false)}
          options={transferUsers}
          title="Transfer Proposal Ownership to another Focal Point"
          onConfirm={confirmTransfer}
        />

        <AssociateKnowledgeModal
          isOpen={isAssociateKnowledgeModalOpen}
          onClose={() => setIsAssociateKnowledgeModalOpen(false)}
          onConfirm={handleAssociateKnowledgeConfirm}
          donorId={formData["Targeted Donor"]?.value}
          outcomeId={formData["Main Outcome"]?.value}
          fieldContextId={formData["Country / Location(s)"]?.value}
          initialSelection={associatedKnowledgeCards}
        />

        <PdfUploadModal
          isOpen={isPdfUploadModalOpen}
          onClose={() => setIsPdfUploadModalOpen(false)}
          onConfirm={handlePdfUpload}
        />

        <ValidationModal
          isOpen={isValidationModalOpen}
          onClose={() => setIsValidationModalOpen(false)}
          missingFields={validationMissingFields}
        />

        <FollowUpModal
          isOpen={showFollowUpModal}
          onClose={() => setShowFollowUpModal(false)}
          onSkip={() => {
            setShowFollowUpModal(false);
            setGenerateLabel("Regenerate");
          }}
          onSaveForLater={() => {
            setShowFollowUpModal(false);
            setGenerateLabel("Regenerate");
          }}
          onRegenerate={handleRegenerateWithFollowUp}
          instruction={followUpInstruction}
          setInstruction={setFollowUpInstruction}
          regenerateCloseIcon={regenerateClose}
          generateIcon={generateIcon}
        />

        <Sidebar
          isMobile={isMobile}
          isMobileMenuOpen={isMobileMenuOpen}
          sidebarOpen={sidebarOpen}
          selectedSection={selectedSectionName}
          proposalTemplate={proposalTemplate}
          proposal={proposal}
          onSectionClick={handleSidebarSectionClick}
          toKebabCase={toKebabCase}
        />

        <main className="Chat_right" ref={topRef} data-testid="chat-main">
          <button className="Chat_menuButton" onClick={() => setIsMobileMenuOpen(p => !p)} data-testid="mobile-menu-button">
            <i className="fa-solid fa-bars"></i>
          </button>

          {proposalStatus !== 'submitted' ? (
            <>
              <Header
                titleName={titleName}
                documentType={documentType}
                setDocumentType={setDocumentType}
                proposalStatus={proposalStatus}
                fileIcon={fileIcon}
                userPrompt={userPrompt}
                setUserPrompt={setUserPrompt}
                formExpanded={formExpanded}
                setFormExpanded={setFormExpanded}
                toKebabCase={toKebabCase}
                renderFormField={(label, disabled) => renderFormField(
                  label, 
                  disabled,
                  formData,
                  handleFormInput,
                  outcomes,
                  donors,
                  filteredFieldContexts,
                  geographicCoverages,
                  newDurations,
                  newBudgetRanges,
                  setNewDurations,
                  setNewBudgetRanges
                )}
                formData={formData}
                setFormData={setFormData}
                outcomes={outcomes}
                donors={donors}
                filteredFieldContexts={filteredFieldContexts}
                geographicCoverages={geographicCoverages}
                newDurations={newDurations}
                setNewDurations={setNewDurations}
                newBudgetRanges={newBudgetRanges}
                setNewBudgetRanges={setNewBudgetRanges}
                handleFormInput={handleFormInput}
              />

              <div className="Chat_inputArea_buttonContainer">
                {Object.keys(proposal).length > 0 && (
                  <div style={{ position: 'relative' }}>
                    <CommonButton
                      onClick={() => {
                        const missing = getMissingFields(userPrompt, formData);
                        if (missing.length > 0) {
                          setValidationMissingFields(missing);
                          setIsValidationModalOpen(true);
                        } else {
                          setIsAssociateKnowledgeModalOpen(true);
                        }
                      }}
                      label="Manage Knowledge"
                      disabled={proposalStatus !== 'draft' || !buttonEnable}
                      className={!buttonEnable ? "inactive" : ""}
                      icon={knowIcon}
                      data-testid="manage-knowledge-button"
                    />
                    {associatedKnowledgeCards.length > 0 && (
                      <div className="associated-knowledge-display" data-testid="associated-knowledge-cards">
                        <h4>Associated Knowledge Cards:</h4>
                        <ul>
                          {associatedKnowledgeCards.map(card => {
                            const title = [
                              card.title,
                              card.donor_name,
                              card.outcome_name,
                              card.field_context_name,
                            ].filter(Boolean).join(' - ');
                            return (
                              <li key={card.id}>
                                <a href={`/knowledge-card/${card.id}`} target="_blank" rel="noopener noreferrer">
                                  {title}
                                </a>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div style={{ marginLeft: 'auto' }}>
                  <CommonButton
                    onClick={handleGenerateClick}
                    icon={generateIcon}
                    label={generateLabel}
                    loading={generateLoading}
                    loadingLabel={generateLabel === "Generate" ? "Generating (~ 2 mins of patience...) " : "Regenerating (~ 2 mins of patience...)"}
                    disabled={generateLoading || (generateLabel === "Generate" && (proposalStatus !== 'draft' || !buttonEnable))}
                    className={(generateLoading || (generateLabel === "Generate" && (proposalStatus !== 'draft' || !buttonEnable))) ? "inactive" : ""}
                    data-testid="generate-button"
                  />
                </div>
              </div>
            </>
          ) : null}

          {sidebarOpen && (
            <>
              <div className='Dashboard_top'>
                <div className='Dashboard_label'>
                  <img className='Dashboard_label_fileIcon' src={resultsIcon} alt="" />
                  Results
                </div>

                {Object.keys(proposal).length > 0 && (
                  <div className='Chat_exportButtons'>
                    <button type="button" onClick={() => handleExport("docx")} data-testid="export-word-button">
                      <img src={word_icon} alt="" />
                      Edit in Word
                    </button>

                    <button type="button" onClick={() => handleExportTables()} data-testid="export-excel-button">
                      <img src={excel_icon} alt="" />
                      Download Tables
                    </button>
                    <button type="button" onClick={() => setIsTransferModalOpen(true)} data-testid="transfer-ownership-button" style={{ marginLeft: '10px', background: '#f5f5f5', color: '#333' }}>
                      Transfer Ownership
                    </button>
                    <div className="Chat_workflow_status_container">
                      {/* Workflow status badges */}
                    </div>
                  </div>
                )}
              </div>

              {proposalStatus === 'submitted' && (
                <div className="contribution-id-container">
                  <label htmlFor="contribution-id">Contribution ID:</label>
                  <p>Only submitted proposal with a confirmed ContributionID are counted as approved</p>
                  <input
                    type="text"
                    id="contribution-id"
                    value={contributionId}
                    onChange={(e) => setContributionId(e.target.value)}
                    data-testid="contribution-id-input"
                  />
                  <CommonButton onClick={handleSaveContributionId} label="Save ID" data-testid="save-contribution-id-button" />
                </div>
              )}

              <ProposalContainer
                proposal={proposal}
                proposalTemplate={proposalTemplate}
                proposalRef={proposalRef}
                proposalStatus={proposalStatus}
                generateLoading={generateLoading}
                selectedSectionName={selectedSectionName}
                isEdit={isEdit}
                isReviewer={isReviewer}
                isAdmin={isAdmin}
                currentUser={currentUser}
                reviews={reviews}
                reviewComments={reviewComments}
                reviewStatus={reviewStatus}
                editorContent={editorContent}
                setEditorContent={setEditorContent}
                isCopied={isCopied}
                setIsCopied={setIsCopied}
                regenerateSectionLoading={regenerateSectionLoading}
                edit={edit}
                save={save}
                copy={copy}
                tick={tick}
                cancel={cancel}
                regenerate={regenerate}
                arrow={arrow}
                toKebabCase={toKebabCase}
                handleEditClick={handleEditClick}
                handleCopyClick={handleCopyClick}
                handleExpanderToggle={handleExpanderToggle}
                handleRegenerateIconClick={handleRegenerateIconClick}
                handleCommentChange={handleCommentChange}
                handleStatusChange={handleStatusChange}
                handleDeleteComment={handleDeleteComment}
                handleReplyToFeedback={handleReplyToFeedback}
                handleSaveResponse={handleSaveResponse}
              />
            </>
          )}
        </main>

        <RegenerateModal
          isOpen={isRegenerateModalOpen}
          onClose={() => {
            setRegenerateSectionLoading(false);
            setRegenerateInput("");
            setIsRegenerateModalOpen(false);
          }}
          onRegenerate={() => handleRegenerateButtonClick()}
          sectionName={selectedSectionName}
          inputValue={regenerateInput}
          setInputValue={setRegenerateInput}
          loading={regenerateSectionLoading}
          generateIcon={generateIcon}
          regenerateCloseIcon={regenerateClose}
        />
      </div>
    </Base>
  );

  // Helper function
  const handleAssociateKnowledgeConfirm = (selectedCards) => {
    setAssociatedKnowledgeCards(selectedCards);
  };
};

export default ChatContainer;

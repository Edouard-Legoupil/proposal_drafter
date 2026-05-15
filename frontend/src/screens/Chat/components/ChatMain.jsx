import React from 'react';
import word_icon from '../../../assets/images/word.svg';
import resultsIcon from '../../../assets/images/Chat_resultsIcon.svg';
import excel_icon from '../../../assets/images/excel.svg';
import CommonButton from '../../../components/CommonButton/CommonButton';
import ProposalContainer from './ProposalContainer';

const statusDetails = {
  draft: {
    text: 'Drafting',
    className: 'status-draft',
    message: 'Initial drafting stage - Author + AI',
  },
  in_review: {
    text: 'Peer Review',
    className: 'status-review',
    message: 'Wait while proposal sent for quality review to other users',
  },
  pre_submission: {
    text: 'Pre-Submission',
    className: 'status-submission',
    message: 'Edit to address the comments from all your reviewers',
  },
  submitted: {
    text: 'Submitted',
    className: 'status-submitted',
    message: 'Non editable Record of Initial version as submitted to donor',
  },
};

const ChatMain = ({
  sidebarOpen,
  proposalStatus,
  proposal,
  proposalTemplate,
  proposalRef,
  generateLoading,
  selectedSectionName,
  isEdit,
  isReviewer,
  isAdmin,
  currentUser,
  reviews,
  reviewComments,
  reviewStatus,
  editorContent,
  setEditorContent,
  isCopied,
  setIsEdit,
  regenerateSectionLoading,
  edit,
  save,
  copy,
  tick,
  cancel,
  regenerate,
  arrow,
  toKebabCase,
  handleEditClick,
  handleCopyClick,
  handleExpanderToggle,
  handleRegenerateIconClick,
  handleCommentChange,
  handleStatusChange,
  handleDeleteComment,
  handleReplyToFeedback,
  handleSaveResponse,
  handleExport,
  handleExportTables,
  setIsTransferModalOpen,
  handleSetStatus,
  handleSubmit,
  handleRevert,
  statusHistory,
  setIsPeerReviewModalOpen,
  handleSaveContributionId,
  contributionId,
  setContributionId,
}) => {
  const workflowStatuses = ['draft', 'in_review', 'pre_submission', 'submitted'];

  return (
    <>
      <div className="Dashboard_top">
        <div className="Dashboard_label">
          <img className="Dashboard_label_fileIcon" src={resultsIcon} alt="" />
          Results
        </div>

        {sidebarOpen && Object.keys(proposal).length > 0 && (
            <div className="Chat_exportButtons">
              <button
                type="button"
                onClick={() => handleExport('docx')}
                data-testid="export-word-button"
              >
                <img src={word_icon} alt="" />
                Edit in Word
              </button>

              <button
                type="button"
                onClick={() => handleExportTables()}
                data-testid="export-excel-button"
              >
                <img src={excel_icon} alt="" />
                Download Tables
              </button>

              <button
                type="button"
              onClick={() => setIsTransferModalOpen(true)}
              data-testid="transfer-ownership-button"
              style={{ marginLeft: '10px', background: '#f5f5f5', color: '#333' }}
            >
              Transfer Ownership
            </button>

            <div className="Chat_workflow_status_container">
              <div className="workflow-stage-box">
                <div className="workflow-stage-box-title">Workflow Stage</div>
                <div className="workflow-badges">
                  {workflowStatuses.map(status => {
                    const isActive = proposalStatus === status;
                    const isClickable =
                      (proposalStatus === 'draft' && (status === 'in_review' || status === 'submitted')) ||
                      (proposalStatus === 'in_review' && (status === 'pre_submission' || status === 'draft')) ||
                      (proposalStatus === 'pre_submission' && status === 'submitted');

                    return (
                      <div key={status} className="status-badge-container">
                        <button
                          type="button"
                          title={statusDetails[status]?.message}
                          className={`status-badge ${statusDetails[status]?.className} ${
                            isActive ? 'active' : 'inactive'
                          }`}
                          onClick={() => {
                            if (status === 'in_review' && proposalStatus === 'draft') {
                              setIsPeerReviewModalOpen(true);
                            }
                            if (status === 'draft' && proposalStatus === 'in_review') {
                              handleSetStatus('draft');
                            }
                            if (
                              status === 'submitted' &&
                              (proposalStatus === 'pre_submission' || proposalStatus === 'draft')
                            ) {
                              handleSubmit();
                            }
                          }}
                          disabled={!isClickable && !isActive}
                          data-testid={`workflow-status-badge-${status}`}
                        >
                          {statusDetails[status]?.text}
                        </button>
                        {statusHistory.includes(status) && !isActive && (
                          <button
                            className="revert-btn"
                            onClick={() => handleRevert(status)}
                            data-testid={`revert-button-${status}`}
                          >
                            Revert
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
                {proposalStatus === 'pre_submission' && (
                  <button
                    className="revert-btn"
                    onClick={() => handleRevert('draft')}
                    data-testid="revert-to-draft-button"
                  >
                    Revert to Draft
                  </button>
                )}
              </div>
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
            onChange={e => setContributionId(e.target.value)}
            data-testid="contribution-id-input"
          />
          <CommonButton
            onClick={handleSaveContributionId}
            label="Save ID"
            data-testid="save-contribution-id-button"
          />
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
        setIsEdit={setIsEdit}
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
  );
};

export default ChatMain;

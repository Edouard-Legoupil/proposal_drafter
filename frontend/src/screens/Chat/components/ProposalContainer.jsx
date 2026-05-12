/**
 * ProposalContainer Component
 * 
 * Renders all proposal sections with their content and options.
 */

import React from 'react';
import Markdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';
import SectionReview from '../../../components/SectionReview/SectionReview';

const ProposalContainer = ({
  proposal,
  proposalTemplate,
  proposalRef,
  proposalStatus,
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
  setIsCopied,
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
  handleSaveResponse
}) => {
  return (
    <div ref={proposalRef} className="Chat_proposalContainer" data-testid="proposal-container">
      {(proposalTemplate ? proposalTemplate.sections.map(s => s.section_name) : Object.keys(proposal)).map((sectionName, i) => {
        const sectionObj = proposal[sectionName];
        const sectionReviews = reviews.filter(r => r.section_name === sectionName);

        if (!sectionObj) return null;
        const kebabSectionName = toKebabCase(sectionName);

        return (
          <div key={i} className="Chat_proposalSection" data-testid={`proposal-section-${kebabSectionName}`}>
            <div className="Chat_sectionHeader" data-testid={`section-header-${kebabSectionName}`}>
              <div className="Chat_sectionTitle" data-testid={`section-title-${kebabSectionName}`}>{sectionName}</div>

              {!generateLoading && sectionObj.content && sectionObj.open && proposalStatus !== 'submitted' && (
                <div className="Chat_sectionOptions" data-testid={`section-options-${kebabSectionName}`}>
                  {!isEdit || (selectedSectionName === sectionName && isEdit) ? (
                    <button
                      type="button"
                      onClick={() => handleEditClick(sectionName)}
                      style={(selectedSectionName === sectionName && isEdit && regenerateSectionLoading) ? { pointerEvents: "none" } : {}}
                      aria-label={`edit-section-${kebabSectionName}`}
                      disabled={isReviewer || proposalStatus === 'in_review'}
                      data-testid={`edit-save-button-${kebabSectionName}`}
                    >
                      <img src={(selectedSectionName === sectionName && isEdit) ? save : edit} alt="" />
                      <span>{(selectedSectionName === sectionName && isEdit) ? "Save" : "Edit"}</span>
                    </button>
                  ) : null}

                  {selectedSectionName === sectionName && isEdit && (
                    <button type="button" onClick={() => setIsEdit(false)} data-testid={`cancel-edit-button-${kebabSectionName}`}>
                      <img src={cancel} alt="" />
                      <span>Cancel</span>
                    </button>
                  )}

                  {!isEdit && (
                    <>
                      <button type="button" onClick={() => handleCopyClick(sectionName, sectionObj.content)} data-testid={`copy-button-${kebabSectionName}`}>
                        <img src={(selectedSectionName === sectionName && isCopied) ? tick : copy} alt="" />
                        <span>{(selectedSectionName === sectionName && isCopied) ? "Copied" : "Copy"}</span>
                      </button>

                      {!isReviewer && (
                        <button type="button" className='Chat_sectionOptions_regenerate' onClick={() => handleRegenerateIconClick(sectionName)} disabled={proposalStatus !== 'draft'} data-testid={`regenerate-button-${kebabSectionName}`}>
                          <img src={regenerate} alt="" />
                          <span>Regenerate</span>
                        </button>
                      )}
                    </>
                  )}
                </div>
              )}

              {sectionObj.content && !(isEdit && selectedSectionName === sectionName) && (
                <div className={`Chat_expanderArrow ${sectionObj.open ? "" : "closed"}`} onClick={() => handleExpanderToggle(sectionName)} data-testid={`section-expander-${kebabSectionName}`}>
                  <img src={arrow} alt="" />
                </div>
              )}
            </div>

            {(sectionObj.open || !sectionObj.content) && (
              <div className='Chat_sectionContent' data-testid={`section-content-${kebabSectionName}`}>
                {sectionObj.content ? (
                  (selectedSectionName === sectionName && isEdit) ? (
                    <textarea value={editorContent} onChange={e => setEditorContent(e.target.value)} aria-label={`editor for ${sectionName}`} data-testid={`section-editor-${kebabSectionName}`} />
                  ) : (
                    <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{sectionObj.content}</Markdown>
                  )
                ) : (
                  <div className='Chat_sectionContent_loading'>
                    <span className='submitButtonSpinner' />
                    <span className='Chat_sectionContent_loading'>Loading</span>
                  </div>
                )}

                {/* Unified SectionReview */}
                <SectionReview
                  key={`${sectionName}-${sectionReviews.length}`}
                  section={sectionName}
                  type="proposal"
                  reviewComment={reviewComments[sectionName]}
                  status={reviewStatus[sectionName]}
                  isReviewEditable={isReviewer || proposalStatus === 'draft'}
                  isAuthorizedToReply={false}
                  onCommentChange={handleCommentChange}
                  onStatusChange={handleStatusChange}
                  onDeleteComment={handleDeleteComment}
                  isOwnerOfComment={true}
                  isAdmin={isAdmin}
                  previousFeedback={(reviews || []).filter(r => r.section_name === sectionName && !['removed', 'fixed'].includes(r.status)).map(review => ({
                    id: review.id,
                    author: review.reviewer_name,
                    review_text: review.review_text,
                    severity: review.severity,
                    type_of_comment: review.type_of_comment,
                    status: review.status,
                    created_at: review.created_at,
                    isOwnedByCurrentUser: review.reviewer_id === currentUser?.id || review.reviewer_id === currentUser?.user_id,
                    replies: review.author_response ? [
                      {
                        author: review.response_author || review.proposal_owner_name || 'Author',
                        text: review.author_response,
                        status: review.status,
                        created_at: review.updated_at || review.created_at
                      }
                    ] : []
                  }))}
                  onReplyToFeedback={handleReplyToFeedback}
                  onSaveReply={handleSaveResponse}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ProposalContainer;

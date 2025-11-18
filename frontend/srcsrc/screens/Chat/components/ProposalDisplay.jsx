import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Review from './Review/Review';
import edit from '../../../assets/images/Chat_edit.svg';
import save from '../../../assets/images/Chat_save.svg';
import cancel from '../../../assets/images/Chat_editCancel.svg';
import copy from '../../../assets/images/Chat_copy.svg';
import tick from '../../../assets/images/Chat_copiedTick.svg';
import regenerate from '../../../assets/images/Chat_regenerate.svg';
import arrow from '../../../assets/images/expanderArrow.svg';

export default function ProposalDisplay({
  proposal,
  proposalTemplate,
  generateLoading,
  isEdit,
  selectedSection,
  isCopied,
  editorContent,
  setEditorContent,
  handleEditClick,
  setIsEdit,
  handleCopyClick,
  handleRegenerateIconClick,
  handleExpanderToggle,
  proposalStatus,
  reviews,
  handleSaveResponse,
}) {
  const toKebabCase = (str) => {
    return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  };

  return (
    <div className="Chat_proposalContainer" data-testid="proposal-container">
      {(proposalTemplate
        ? proposalTemplate.sections.map((s) => s.section_name)
        : Object.keys(proposal)
      ).map((sectionName, i) => {
        const sectionObj = proposal[sectionName];
        const sectionReviews = reviews.filter(
          (r) => r.section_name === sectionName
        );

        if (!sectionObj) return null;
        const kebabSectionName = toKebabCase(sectionName);

        return (
          <div
            key={i}
            className="Chat_proposalSection"
            data-testid={`proposal-section-${kebabSectionName}`}
          >
            <div
              className="Chat_sectionHeader"
              data-testid={`section-header-${kebabSectionName}`}
            >
              <div
                className="Chat_sectionTitle"
                data-testid={`section-title-${kebabSectionName}`}
              >
                {sectionName}
              </div>

              {!generateLoading &&
              sectionObj.content &&
              sectionObj.open &&
              proposalStatus !== 'submitted' ? (
                <div
                  className="Chat_sectionOptions"
                  data-testid={`section-options-${kebabSectionName}`}
                >
                  {!isEdit || (selectedSection === i && isEdit) ? (
                    <button
                      type="button"
                      onClick={() => handleEditClick(i)}
                      style={
                        selectedSection === i && isEdit && regenerateSectionLoading
                          ? { pointerEvents: 'none' }
                          : {}
                      }
                      aria-label={`edit-section-${i}`}
                      disabled={proposalStatus === 'in_review'}
                      data-testid={`edit-save-button-${kebabSectionName}`}
                    >
                      <img src={selectedSection === i && isEdit ? save : edit} />
                      <span>{selectedSection === i && isEdit ? 'Save' : 'Edit'}</span>
                    </button>
                  ) : (
                    ''
                  )}

                  {selectedSection === i && isEdit ? (
                    <button
                      type="button"
                      onClick={() => setIsEdit(false)}
                      data-testid={`cancel-edit-button-${kebabSectionName}`}
                    >
                      <img src={cancel} />
                      <span>Cancel</span>
                    </button>
                  ) : (
                    ''
                  )}

                  {!isEdit ? (
                    <>
                      <button
                        type="button"
                        onClick={() => handleCopyClick(i, sectionObj.content)}
                        data-testid={`copy-button-${kebabSectionName}`}
                      >
                        <img src={selectedSection === i && isCopied ? tick : copy} />
                        <span>{selectedSection === i && isCopied ? 'Copied' : 'Copy'}</span>
                      </button>

                      <button
                        type="button"
                        className="Chat_sectionOptions_regenerate"
                        onClick={() => handleRegenerateIconClick(i)}
                        disabled={proposalStatus !== 'draft'}
                        data-testid={`regenerate-button-${kebabSectionName}`}
                      >
                        <img src={regenerate} />
                        <span>Regenerate</span>
                      </button>
                    </>
                  ) : (
                    ''
                  )}
                </div>
              ) : (
                ''
              )}

              {sectionObj.content && !(isEdit && selectedSection === i) ? (
                <div
                  className={`Chat_expanderArrow ${sectionObj.open ? '' : 'closed'}`}
                  onClick={() => handleExpanderToggle(i)}
                  data-testid={`section-expander-${kebabSectionName}`}
                >
                  <img src={arrow} />
                </div>
              ) : (
                ''
              )}
            </div>

            {sectionObj.open || !sectionObj.content ? (
              <div
                className="Chat_sectionContent"
                data-testid={`section-content-${kebabSectionName}`}
              >
                {sectionObj.content ? (
                  selectedSection === i && isEdit ? (
                    <textarea
                      value={editorContent}
                      onChange={(e) => setEditorContent(e.target.value)}
                      aria-label={`editor for ${sectionName}`}
                      data-testid={`section-editor-${kebabSectionName}`}
                    />
                  ) : (
                    <Markdown remarkPlugins={[remarkGfm]}>
                      {sectionObj.content}
                    </Markdown>
                  )
                ) : (
                  <div className="Chat_sectionContent_loading">
                    <span className="submitButtonSpinner" />
                    <span className="Chat_sectionContent_loading">Loading</span>
                  </div>
                )}
              </div>
            ) : (
              ''
            )}

            {(proposalStatus === 'pre_submission' ||
              proposalStatus === 'submission') &&
            reviews.length > 0 && (
              <div
                className="reviews-container"
                data-testid={`reviews-container-${kebabSectionName}`}
              >
                <h4>Peer Reviews</h4>
                {reviews
                  .filter((r) => r.section_name === sectionName)
                  .map((review) => (
                    <Review
                      key={review.id}
                      review={review}
                      onSaveResponse={handleSaveResponse}
                    />
                  ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

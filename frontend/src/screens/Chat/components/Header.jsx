/**
 * Header Component
 *
 * Displays the chat header with title, document type switcher, main prompt, and parameter form.
 */

import React from 'react';
import arrow from "../../../assets/images/expanderArrow.svg";

const Header = ({
  titleName,
  documentType,
  setDocumentType,
  proposalStatus,
  fileIcon,
  userPrompt,
  setUserPrompt,
  formExpanded,
  setFormExpanded,
  renderFormField,
  formData,
  setFormData
}) => {
  return (
    <>
      {/* Title */}
      <div className='Dashboard_top'>
        <div className='Dashboard_label' data-testid="chat-title">
          <img className='Dashboard_label_fileIcon' src={fileIcon} alt="" />
          {titleName}
        </div>
      </div>

      {/* Input Area with Doc Type Switcher and Main Prompt */}
      <div className="Chat_inputArea">
        <div className="Chat_docTypeSwitcher" data-testid="doc-type-switcher">
          <button
            type="button"
            className={`Chat_docTypeButton ${documentType === 'proposal' ? 'active' : ''}`}
            onClick={() => proposalStatus === 'draft' && setDocumentType('proposal')}
            disabled={proposalStatus !== 'draft'}
            data-testid="doc-type-proposal-button"
          >
            Proposal
          </button>
          <button
            type="button"
            className={`Chat_docTypeButton ${documentType === 'concept note' ? 'active' : ''}`}
            onClick={() => proposalStatus === 'draft' && setDocumentType('concept note')}
            disabled={proposalStatus !== 'draft'}
            data-testid="doc-type-concept-note-button"
          >
            Concept Note
          </button>
        </div>

        {/* Project Short Name Field */}
        {renderFormField("Project Draft Short name", proposalStatus !== 'draft')}

        {/* Main Prompt Textarea */}
        <textarea
          id="main-prompt"
          name="main-prompt"
          value={userPrompt}
          onChange={e => setUserPrompt(e.target.value)}
          placeholder='Provide as much details as possible on your initial project idea!'
          className='Chat_inputArea_prompt'
          disabled={proposalStatus !== 'draft'}
          data-testid="main-prompt"
        />

        {/* Specify Parameters Button */}
        <span
          onClick={() => proposalStatus === 'draft' && setFormExpanded(p => !p)}
          className={`Chat_inputArea_additionalDetails ${formExpanded && "expanded"} ${proposalStatus !== 'draft' ? 'disabled' : ''}`}
          data-testid="specify-parameters-expander"
        >
          Specify Parameters
          <img src={arrow} alt="Arrow" />
        </span>

        {/* Parameter Form - appears when expanded */}
        {formExpanded && (
          <form className='Chat_form' data-testid="chat-form">
            <div className='Chat_form_group'>
              <div className="tooltip-container">
                <h3 className='Chat_form_group_title'>Identify Potential Interventions</h3>
                <span className="tooltip-text">surface Relevant Policies, Strategies and past Evaluation Recommendations</span>
              </div>
              {renderFormField("Main Outcome", proposalStatus !== 'draft')}
              {renderFormField("Beneficiaries Profile", proposalStatus !== 'draft')}
              {renderFormField("Potential Implementing Partner", proposalStatus !== 'draft')}
            </div>

            <div className='Chat_form_group'>
              <div className="tooltip-container">
                <h3 className='Chat_form_group_title'>Define Field Context</h3>
                <span className="tooltip-text">surface Situation Analysis and Needs Assessment</span>
              </div>
              {renderFormField("Geographical Scope", proposalStatus !== 'draft')}

              <div className="Chat_form_inputContainer" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
                <input
                  type="checkbox"
                  id="multiple-countries"
                  checked={formData["multiple countries"]?.value || false}
                  onChange={e => {
                    const isChecked = e.target.checked;
                    setFormData(prev => ({
                      ...prev,
                      "multiple countries": { ...prev["multiple countries"], value: isChecked },
                      "Country / Location(s)": { ...prev["Country / Location(s)"], value: isChecked ? [] : "" }
                    }));
                  }}
                  disabled={proposalStatus !== 'draft'}
                />
                <label htmlFor="multiple-countries" className="Chat_form_inputLabel" style={{ marginBottom: 0 }}>Multiple Countries</label>
              </div>
              {renderFormField("Country / Location(s)", proposalStatus !== 'draft')}
            </div>

            <div className='Chat_form_group'>
              <div className="tooltip-container">
                <h3 className='Chat_form_group_title'>Tailor Funding Request</h3>
                <span className="tooltip-text">surface Donor profile and apply Formal Requirement for Submission</span>
              </div>
              {renderFormField("Budget Range", proposalStatus !== 'draft')}
              {renderFormField("Duration", proposalStatus !== 'draft')}

              <div className="Chat_form_inputContainer" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
                <input
                  type="checkbox"
                  id="multiple-donors"
                  checked={formData["multiple donors"]?.value || false}
                  onChange={e => {
                    const isChecked = e.target.checked;
                    setFormData(prev => ({
                      ...prev,
                      "multiple donors": { ...prev["multiple donors"], value: isChecked },
                      "Targeted Donor": { ...prev["Targeted Donor"], value: isChecked ? [] : (prev["Targeted Donor"]?.value || "") }
                    }));
                  }}
                  disabled={proposalStatus !== 'draft'}
                />
                <label htmlFor="multiple-donors" className="Chat_form_inputLabel" style={{ marginBottom: 0 }}>Multiple Donors</label>
              </div>
              {renderFormField("Targeted Donor", proposalStatus !== 'draft')}
            </div>
          </form>
        )}
      </div>
    </>
  );
};

export default Header;

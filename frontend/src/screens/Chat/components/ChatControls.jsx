import React from 'react';
import CommonButton from '../../../components/CommonButton/CommonButton';
import knowIcon from '../../../assets/images/knowIcon.svg';
import generateIcon from '../../../assets/images/generateIcon.svg';

const ChatControls = ({
  proposal,
  proposalStatus,
  buttonEnable,
  getMissingFields,
  setValidationMissingFields,
  setIsValidationModalOpen,
  setIsAssociateKnowledgeModalOpen,
  associatedKnowledgeCards,
  handleGenerateClick,
  generateLabel,
  generateLoading,
  userPrompt,
}) => {
  const showManageButton = Object.keys(proposal).length > 0;

  const handleManageClick = () => {
    const missing = getMissingFields(userPrompt);
    if (missing.length > 0) {
      setValidationMissingFields(missing);
      setIsValidationModalOpen(true);
    } else {
      setIsAssociateKnowledgeModalOpen(true);
    }
  };

  return (
    <div className="Chat_inputArea_buttonContainer">
      {showManageButton && (
        <div style={{ position: 'relative' }}>
          <CommonButton
            onClick={handleManageClick}
            label="Manage Knowledge"
            disabled={proposalStatus !== 'draft' || !buttonEnable}
            className={!buttonEnable ? 'inactive' : ''}
            icon={knowIcon}
            data-testid="manage-knowledge-button"
          />
          {associatedKnowledgeCards && associatedKnowledgeCards.length > 0 && (
            <div className="associated-knowledge-display" data-testid="associated-knowledge-cards">
              <h4>Associated Knowledge Cards:</h4>
              <ul>
                {associatedKnowledgeCards.map(card => {
                  const title = [
                    card.title,
                    card.donor_name,
                    card.outcome_name,
                    card.field_context_name,
                  ]
                    .filter(Boolean)
                    .join(' - ');
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
          loadingLabel={
            generateLabel === 'Generate'
              ? 'Generating (~ 2 mins of patience...) '
              : 'Regenerating (~ 2 mins of patience...)'
          }
          disabled={
            generateLoading || (generateLabel === 'Generate' && (proposalStatus !== 'draft' || !buttonEnable))
          }
          className={
            generateLoading || (generateLabel === 'Generate' && (proposalStatus !== 'draft' || !buttonEnable))
              ? 'inactive'
              : ''
          }
          data-testid="generate-button"
        />
      </div>
    </div>
  );
};

export default ChatControls;

/**
 * FollowUpModal Component
 * Shows when users want to regenerate a proposal with additional instructions
 */

import React from 'react';
import CommonButton from '../../../../components/CommonButton/CommonButton';

const FollowUpModal = ({
  isOpen,
  onClose,
  onSkip,
  onSaveForLater,
  onRegenerate,
  instruction,
  setInstruction,
  regenerateCloseIcon,
  generateIcon
}) => {
  return (
    <dialog 
      open={isOpen} 
      className="Chat_regenerate" 
      style={{ 
        height: 'auto', 
        maxHeight: '80vh', 
        top: '10%', 
        width: '60vw', 
        maxWidth: '800px' 
      }} 
      data-testid="followup-modal"
    >
      <header className="Chat_regenerate_header">
        Provide Follow-up Instructions
        <img 
          src={regenerateCloseIcon} 
          alt="" 
          onClick={onClose} 
          style={{ cursor: 'pointer' }} 
        />
      </header>
      <main className="Chat_right" style={{ padding: '20px' }}>
        <p style={{ marginBottom: '15px', color: '#666' }}>
          Please provide any follow-up instructions or refinements you'd like to make.
          The AI will use the existing content as context and apply your instructions to improve it.
        </p>
        <textarea
          id="followup-instruction"
          name="followup-instruction"
          value={instruction}
          onChange={e => setInstruction(e.target.value)}
          className='Chat_inputArea_prompt'
          placeholder="e.g., 'Make the budget section more detailed', 'Focus more on gender equality', 'Revise the timeline to be more realistic'..."
          style={{ minHeight: '100px', marginBottom: '20px' }}
          data-testid="followup-instruction-input"
        />
        <div className="Chat_inputArea_buttonContainer" style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <CommonButton 
            onClick={onSkip} 
            label="Skip" 
            data-testid="followup-skip-button" 
          />
          <CommonButton
            onClick={onSaveForLater}
            label="Save for Later"
            data-testid="followup-save-button"
          />
          <CommonButton
            icon={generateIcon}
            onClick={onRegenerate}
            label="Regenerate Now"
            disabled={!instruction}
            data-testid="followup-regenerate-button"
          />
        </div>
      </main>
    </dialog>
  );
};

export default FollowUpModal;

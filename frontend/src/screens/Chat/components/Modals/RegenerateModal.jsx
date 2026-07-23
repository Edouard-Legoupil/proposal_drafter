/**
 * Regenerate Section Modal Component
 *
 * Shown when users want to regenerate a specific section of a proposal.
 */

import React from 'react';
import CommonButton from '../../../../components/CommonButton/CommonButton';

const RegenerateModal = ({
  isOpen,
  onClose,
  onRegenerate,
  sectionName,
  inputValue,
  setInputValue,
  loading,
  generateIcon,
  regenerateCloseIcon
}) => {
  return (
    <dialog
      open={isOpen}
      className='Chat_regenerate'
      data-testid="regenerate-dialog"
    >
      <header className='Chat_regenerate_header'>
        Regenerate — {sectionName || "Section"}
        <button
          onClick={onClose}
          aria-label="Close"
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '5px' }}
          data-testid="regenerate-dialog-close-button"
        >
          <img
            src={regenerateCloseIcon}
            alt=""
            style={{ width: '24px', height: '24px' }}
          />
        </button>
      </header>

      <main className='Chat_right'>
        <section className='Chat_inputArea'>
          <textarea
            id="regenerate-prompt"
            name="regenerate-prompt"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            className='Chat_inputArea_prompt'
            data-testid="regenerate-dialog-prompt-input"
          />

          <div className="Chat_inputArea_buttonContainer" style={{ marginTop: "20px" }}>
            <CommonButton
              icon={generateIcon}
              onClick={onRegenerate}
              label="Regenerate"
              loading={loading}
              loadingLabel="Regenerating"
              disabled={!inputValue}
              data-testid="regenerate-dialog-regenerate-button"
            />
          </div>
        </section>
      </main>
    </dialog>
  );
};

export default RegenerateModal;

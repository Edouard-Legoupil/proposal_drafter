/**
 * ProgressModal Component
 * Shows generation progress with percentage and status messages
 */

import React from 'react';
import CommonButton from '../../../../components/CommonButton/CommonButton';

const ProgressModal = ({ 
  isOpen, 
  progress = 0,
  message = '',
  onClose
}) => {
  // Determine if generation failed based on message
  const isFailed = message?.includes('failed') || message?.includes('Failed');
  
  return (
    <dialog open={isOpen} className="Chat_regenerate" style={{ height: '360px' }}>
      <header className="Chat_regenerate_header" style={{ padding: '20px' }}>
        <div
          style={{
            width: '100%',
            height: '30px',
            borderRadius: '10px',
            backgroundColor: '#e0e0e0',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: isFailed ? '#ff4444' : '#4CAF50',
              transition: 'width 0.3s ease',
              borderRadius: '10px'
            }}
          />
        </div>
      </header>
      <main className="Chat_right" style={{ padding: '20px' }}>
        <p style={{ textAlign: 'center', fontWeight: 600 }}>
          {message}
        </p>
        <p style={{ textAlign: 'center', marginTop: '10px' }}>
          {progress}%
        </p>
        {isFailed && (
          <div className="Chat_inputArea_buttonContainer" style={{ justifyContent: 'center' }}>
            <CommonButton onClick={onClose} label="Close" />
          </div>
        )}
      </main>
    </dialog>
  );
};

export default ProgressModal;

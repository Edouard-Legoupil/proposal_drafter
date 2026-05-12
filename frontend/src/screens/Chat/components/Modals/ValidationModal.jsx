/**
 * ValidationModal Component
 * Shows when required form fields are missing
 */

import React from 'react';
import CommonButton from '../../../../components/CommonButton/CommonButton';

const ValidationModal = ({ isOpen, onClose, missingFields = [] }) => {
  return (
    <dialog open={isOpen} className="Chat_regenerate" style={{ height: 'auto', maxHeight: '80vh', top: '10%' }}>
      <header className="Chat_regenerate_header">
        Missing Required Fields
      </header>
      <main className="Chat_right" style={{ padding: '20px' }}>
        <p style={{ marginBottom: '15px' }}>The following mandatory parameters are missing:</p>
        <ul style={{ listStyleType: 'disc', paddingLeft: '20px', marginBottom: '20px', color: '#141419' }}>
          {missingFields.map((field, index) => (
            <li key={index} style={{ marginBottom: '5px' }}>{field}</li>
          ))}
        </ul>
        <div className="Chat_inputArea_buttonContainer">
          <CommonButton onClick={onClose} label="Close" />
        </div>
      </main>
    </dialog>
  );
};

export default ValidationModal;

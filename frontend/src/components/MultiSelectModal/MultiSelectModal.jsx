import './MultiSelectModal.css'

import { useState } from 'react';

export default function MultiSelectModal({ isOpen, onClose, options, selectedOptions, onSelectionChange, title, onConfirm, showDeadline = false }) {
  const [deadline, setDeadline] = useState('');

  if (!isOpen) {
    return null;
  }

  const handleConfirm = () => {
    onConfirm({ selectedUsers: selectedOptions, deadline });
    onClose();
  };

  const handleCheckboxChange = (option) => {
    const optionValue = option.id || option;
    const newSelection = selectedOptions.includes(optionValue)
      ? selectedOptions.filter(item => item !== optionValue)
      : [...selectedOptions, optionValue];
    onSelectionChange(newSelection);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{title || 'Select Options'}</h2>
        <div className="modal-options">
          {options.map(option => {
            const optionValue = option.id || option;
            const optionLabel = option.name || option;
            return (
              <div key={optionValue} className="modal-option">
                <input
                  type="checkbox"
                  id={optionValue}
                  value={optionValue}
                  checked={selectedOptions.includes(optionValue)}
                  onChange={() => handleCheckboxChange(option)}
                  data-testid={`user-select-checkbox-${optionValue}`}
                />
                <label htmlFor={optionValue}>{optionLabel}</label>
              </div>
            );
          })}
        </div>
        {showDeadline && (
          <div className="modal-deadline">
            <label htmlFor="deadline">Deadline:</label>
            <input type="date" id="deadline" value={deadline} onChange={e => setDeadline(e.target.value)} data-testid="deadline-input" />
          </div>
        )}
        <div className="modal-actions">
          {onConfirm && <button onClick={handleConfirm} disabled={selectedOptions.length === 0} data-testid="confirm-button">Confirm</button>}
        </div>
      </div>
    </div>
  );
}

import './MultiSelectModal.css'

import { useState } from 'react';

export default function MultiSelectModal({ isOpen, onClose, options, selectedOptions, onSelectionChange, title, onConfirm, showDeadline = false }) {
  const [deadline, setDeadline] = useState('');
  const today = new Date().toISOString().split('T')[0];

  if (!isOpen) {
    return null;
  }

  const handleConfirm = () => {
    if (new Date(deadline) > new Date()) {
      onConfirm({ selectedUsers: selectedOptions, deadline });
      onClose();
    }
  };

  const handleCheckboxChange = (option) => {
    const optionValue = option.id || option;
    const newSelection = selectedOptions.includes(optionValue)
      ? selectedOptions.filter(item => item !== optionValue)
      : [...selectedOptions, optionValue];
    onSelectionChange(newSelection);
  };

  return (
    <div className="modal-overlay" data-testid="multi-select-modal-overlay">
      <div className="modal-content" data-testid="multi-select-modal-content">
        <h2 data-testid="multi-select-modal-title">{title || 'Select Options'}</h2>
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
                <label htmlFor={optionValue} data-testid={`user-select-label-${optionValue}`}>{optionLabel}</label>
              </div>
            );
          })}
        </div>
        {showDeadline && (
          <div className="modal-deadline">
            <label htmlFor="deadline">Deadline:</label>
            <input type="date" id="deadline" value={deadline} min={today} onChange={e => setDeadline(e.target.value)} data-testid="deadline-input" />
          </div>
        )}
        <div className="modal-actions">
          {onConfirm && <button onClick={handleConfirm} disabled={selectedOptions.length === 0 || !deadline || new Date(deadline) <= new Date()} data-testid="confirm-button">Confirm</button>}
          <button onClick={onClose} data-testid="close-button">Close</button>
        </div>
      </div>
    </div>
  );
}

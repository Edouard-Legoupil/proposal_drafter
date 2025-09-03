import './SingleSelectUserModal.css'
import { useState } from 'react';

export default function SingleSelectUserModal({ isOpen, onClose, options, title, onConfirm }) {
  const [selectedUser, setSelectedUser] = useState(null);

  if (!isOpen) {
    return null;
  }

  const handleConfirm = () => {
    if (selectedUser) {
      onConfirm(selectedUser);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{title || 'Select a User'}</h2>
        <div className="modal-options">
          {options.map(option => {
            const optionValue = option.id || option;
            const optionLabel = option.name || option;
            return (
              <div key={optionValue} className="modal-option">
                <input
                  type="radio"
                  id={optionValue}
                  name="user-select"
                  value={optionValue}
                  checked={selectedUser === optionValue}
                  onChange={() => setSelectedUser(optionValue)}
                />
                <label htmlFor={optionValue}>{optionLabel}</label>
              </div>
            );
          })}
        </div>
        <div className="modal-actions">
          <button onClick={onClose}>Close</button>
          <button onClick={handleConfirm} disabled={!selectedUser}>Confirm</button>
        </div>
      </div>
    </div>
  );
}

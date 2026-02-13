import './SingleSelectUserModal.css'
import { useState } from 'react';

export default function SingleSelectUserModal({ isOpen, onClose, options, title, onConfirm }) {
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) {
    return null;
  }

  const handleConfirm = () => {
    if (selectedUser) {
      onConfirm(selectedUser);
      onClose();
    }
  };

  const filteredOptions = options.filter(option => {
    const name = option.name || (typeof option === 'string' ? option : '');
    const team = option.team || '';
    const searchable = `${name} ${team}`.toLowerCase();
    return searchable.includes(searchTerm.toLowerCase());
  });

  return (
    <div className="modal-overlay" data-testid="single-select-user-modal-overlay">
      <div className="modal-content" data-testid="single-select-user-modal-content">
        <h2 data-testid="single-select-user-modal-title">{title || 'Select a User'}</h2>

        <div className="modal-search">
          <input
            type="text"
            placeholder="Filter users by name or team..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            data-testid="user-filter-input"
          />
        </div>


        <div className="modal-options">
          {filteredOptions.length > 0 ? (
            // Group by team
            Object.entries(filteredOptions.reduce((acc, option) => {
              const team = option.team || 'Unassigned';
              if (!acc[team]) acc[team] = [];
              acc[team].push(option);
              return acc;
            }, {})).sort().map(([team, teamOptions]) => (
              <div key={team} className="team-group">
                <h4 className="team-header">{team}</h4>
                {teamOptions.map(option => {
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
                        data-testid={`user-select-radio-${optionValue}`}
                      />
                      <label htmlFor={optionValue} data-testid={`user-select-label-${optionValue}`}>{optionLabel}</label>
                    </div>
                  );
                })}
              </div>
            ))
          ) : (
            <p className="no-users-label">No users found matching your search.</p>
          )}
        </div>
        <div className="modal-actions">
          <button onClick={onClose} data-testid="close-button">Close</button>
          <button onClick={handleConfirm} disabled={!selectedUser} data-testid="confirm-button">Confirm</button>
        </div>
      </div>
    </div>
  );
}

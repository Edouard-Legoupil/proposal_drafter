import './AssociateKnowledgeModal.css'

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function AssociateKnowledgeModal({ isOpen, onClose, onConfirm, donorId, outcomeId, fieldContextId, initialSelection = [] }) {
  const navigate = useNavigate();
  const [options, setOptions] = useState([]);
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [initialSelectedOptions, setInitialSelectedOptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const initialIds = initialSelection.map(c => c.id);
      setSelectedOptions(initialIds);
      setInitialSelectedOptions(initialIds);
      setIsLoading(true);
      const queryParams = new URLSearchParams();
      if (donorId) queryParams.append('donor_id', donorId);
      if (Array.isArray(outcomeId)) {
        outcomeId.forEach(id => id && queryParams.append('outcome_id', id));
      } else if (outcomeId) {
        queryParams.append('outcome_id', outcomeId);
      }
      if (fieldContextId) queryParams.append('field_context_id', fieldContextId);

      fetch(`${API_BASE_URL}/knowledge-cards?${queryParams.toString()}`, {
        credentials: 'include'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          setOptions(data.knowledge_cards || []);
          setIsLoading(false);
        })
        .catch(error => {
          console.error("Error fetching knowledge cards:", error);
          setIsLoading(false);
        });
    }
  }, [isOpen, donorId, outcomeId, fieldContextId, initialSelection]);

  if (!isOpen) {
    return null;
  }

  const handleConfirm = () => {
    const selectedCards = options.filter(option => selectedOptions.includes(option.id));
    onConfirm(selectedCards);
    onClose();
  };

  const handleCheckboxChange = (optionId) => {
    const newSelection = selectedOptions.includes(optionId)
      ? selectedOptions.filter(item => item !== optionId)
      : [...selectedOptions, optionId];
    setSelectedOptions(newSelection);
  };

  const selectionHasChanged = () => {
    if (selectedOptions.length !== initialSelectedOptions.length) {
      return true;
    }
    const sortedCurrent = [...selectedOptions].sort();
    const sortedInitial = [...initialSelectedOptions].sort();
    return sortedCurrent.join(',') !== sortedInitial.join(',');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>Associate Knowledge</h2>
        <div className="modal-options">
          {isLoading ? (
            <p>Loading...</p>
          ) : options.length > 0 ? (
            options.map(option => (
              <div key={option.id} className="modal-option">
                <input
                  type="checkbox"
                  id={option.id}
                  value={option.id}
                  checked={selectedOptions.includes(option.id)}
                  onChange={() => handleCheckboxChange(option.id)}
                />
                <div>
                  <label htmlFor={option.id}><strong>{option.title}</strong></label>
                  <div className="linked-element">
                    {option.donor_name && <span>Donor: {option.donor_name}</span>}
                    {option.outcome_name && <span>Outcome: {option.outcome_name}</span>}
                    {option.field_context_name && <span>Field Context: {option.field_context_name}</span>}
                  </div>
                  <p>{option.summary}</p>
                </div>
              </div>
            ))
          ) : (
            <p>No knowledge cards found for the selected criteria.</p>
          )}
        </div>
        <div className="modal-actions">
          <button onClick={() => navigate('/knowledge-card/new')}>Create New Knowledge Card</button>  
          <div>
            <button onClick={onClose}>Cancel </button> 
            {onConfirm && <button onClick={handleConfirm} disabled={!selectionHasChanged()}>Confirm</button>}
          </div>
        </div>
      </div>
    </div>
  );
}

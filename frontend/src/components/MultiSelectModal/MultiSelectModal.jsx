import './MultiSelectModal.css'

export default function MultiSelectModal({ isOpen, onClose, options, selectedOptions, onSelectionChange, title, onConfirm }) {
  if (!isOpen) {
    return null;
  }

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
                />
                <label htmlFor={optionValue}>{optionLabel}</label>
              </div>
            );
          })}
        </div>
        <div className="modal-actions">
          <button onClick={onClose}>Close</button>
          {onConfirm && <button onClick={onConfirm}>Confirm</button>}
        </div>
      </div>
    </div>
  );
}

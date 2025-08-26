import './MultiSelectModal.css'

export default function MultiSelectModal({ isOpen, onClose, options, selectedOptions, onSelectionChange }) {
  if (!isOpen) {
    return null;
  }

  const handleCheckboxChange = (option) => {
    const newSelection = selectedOptions.includes(option)
      ? selectedOptions.filter(item => item !== option)
      : [...selectedOptions, option];
    onSelectionChange(newSelection);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Select Outcomes</h2>
        <div className="modal-options">
          {options.map(option => (
            <div key={option} className="modal-option">
              <input
                type="checkbox"
                id={option}
                value={option}
                checked={selectedOptions.includes(option)}
                onChange={() => handleCheckboxChange(option)}
              />
              <label htmlFor={option}>{option}</label>
            </div>
          ))}
        </div>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

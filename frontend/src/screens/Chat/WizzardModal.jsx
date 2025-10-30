// frontend/src/screens/Chat/WizzardModal.jsx
import React, { useState } from 'react';
import './WizzardModal.css';

const WizzardModal = ({ isOpen, onClose, formData, userPrompt }) => {
  const [analysis, setAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/wizzard/get-insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          form_data: formData,
          prompt: userPrompt,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analysis');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="wizzard-modal-overlay">
      <div className="wizzard-modal">
        <h2>Proposal Wizzard</h2>
        <p>Get an analysis of your proposal's parameters and prompt, and receive suggestions for improvement.</p>
        <button onClick={fetchAnalysis} disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Analyze My Proposal'}
        </button>
        {error && <div className="error-message">{error}</div>}
        {analysis && (
          <div className="analysis-container">
            <h3>Analysis Summary</h3>
            <p>{analysis.analysis_summary}</p>
            <p><strong>Success Likelihood:</strong> {Math.round(analysis.success_likelihood * 100)}%</p>

            <h3>Suggested Improvements</h3>
            <div>
              <h4>Revised Parameters:</h4>
              <ul>
                <li><strong>Donor:</strong> {analysis.suggested_donor_id}</li>
                <li><strong>Outcome:</strong> {analysis.suggested_outcome_id}</li>
                <li><strong>Field Context:</strong> {analysis.suggested_field_context_id}</li>
                <li><strong>Budget Range:</strong> {analysis.suggested_budget_range}</li>
              </ul>
            </div>

            <div>
              <h4>Revised Prompt:</h4>
              <p>{analysis.suggested_prompt}</p>
            </div>
          </div>
        )}
        <button onClick={onClose} className="close-button">Close</button>
      </div>
    </div>
  );
};

export default WizzardModal;

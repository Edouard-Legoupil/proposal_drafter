import React, { useState } from 'react';
import './Review.css';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Review = ({ review, onSaveResponse }) => {
  const [response, setResponse] = useState(review.author_response || '');

  const handleResponseChange = (e) => {
    setResponse(e.target.value);
  };

  const handleSave = () => {
    onSaveResponse(review.id, response);
  };

  return (
    <div className="review-container">
      <div className="review-comment">
        <p className="reviewer-name">{review.reviewer_name} commented:</p>
        <Markdown remarkPlugins={[remarkGfm]}>{review.review_text}</Markdown>
      </div>
      <div className="author-response">
        <textarea
          value={response}
          onChange={handleResponseChange}
          onBlur={handleSave}
          placeholder="Type your response here..."
        />
      </div>
    </div>
  );
};

export default Review;
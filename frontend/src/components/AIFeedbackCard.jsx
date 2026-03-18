import React from 'react';
import { Sparkles, ShieldCheck, HeartPulse } from 'lucide-react';

const AIFeedbackCard = ({ feedback }) => {
  if (!feedback) return null;

  // Simple parsing to split prevention and cure if they are formatted with typical markdown lists or headers
  // For basic display, we'll render the raw text, but we can try to find sections
  
  // Clean up markdown bolding for simpler display if needed, but standard text is fine
  const formatText = (text) => {
      // Remove ** markdown bolding and replace newlines with breaks
      const cleanText = text.replace(/\*\*/g, '');
      return cleanText.split('\n').map((str, index) => (
          <React.Fragment key={index}>
              {str}
              <br />
          </React.Fragment>
      ));
  }

  return (
    <div className="ai-feedback-container animate-fade-in" style={{ animationDelay: '0.4s', animationFillMode: 'both' }}>
      <div className="ai-feedback-header">
        <div className="ai-icon-wrap">
          <Sparkles size={24} color="#3ec97e" />
        </div>
        <h2 className="ai-title">AI Agricultural Assistant</h2>
      </div>
      
      <div className="ai-content-body">
        <p className="ai-intro">Based on the diagnosis, here is our recommended action plan:</p>
        
        <div className="ai-feedback-box">
            {formatText(feedback)}
        </div>
      </div>
    </div>
  );
};

export default AIFeedbackCard;

import React, { useEffect, useState } from 'react';
import { Activity, CheckCircle, AlertTriangle } from 'lucide-react';

const ResultCard = ({ result }) => {
  const [animatedConfidence, setAnimatedConfidence] = useState(0);

  useEffect(() => {
    // Animate the confidence bar on mount
    const timer = setTimeout(() => {
      setAnimatedConfidence(result.confidence * 100);
    }, 100);
    return () => clearTimeout(timer);
  }, [result.confidence]);

  if (!result) return null;

  const isHealthy = result.prediction.toLowerCase().includes('healthy');
  
  // Choose color based on health status and confidence
  const getConfidenceColor = () => {
    if (isHealthy) return '#2ecc71'; // Green for healthy
    if (result.confidence > 0.8) return '#ef4444'; // Red for high confidence disease
    return '#f59e0b'; // Yellow/Orange for lower confidence disease
  };

  const confidenceColor = getConfidenceColor();

  return (
    <div className="result-container">
      <div className="result-header">
        <div className="result-icon">
          <Activity size={32} color={isHealthy ? '#2ecc71' : '#ef4444'} />
        </div>
        <div>
          <h2 className="result-title">Analysis Complete</h2>
          <div className={`disease-name ${isHealthy ? 'healthy' : ''}`}>
            {result.formatted_prediction}
          </div>
        </div>
      </div>

      <div className="confidence-section">
        <div className="confidence-header">
          <span>Confidence Score</span>
          <span style={{ fontWeight: 600, color: confidenceColor }}>
            {(result.confidence * 100).toFixed(1)}%
          </span>
        </div>
        
        <div className="confidence-bar-bg">
          <div 
            className="confidence-bar-fill"
            style={{ 
              width: `${animatedConfidence}%`,
              backgroundColor: confidenceColor,
              boxShadow: `0 0 10px ${confidenceColor}`
            }}
          />
        </div>
      </div>

      <div className={`status-badge ${isHealthy ? 'status-healthy' : 'status-disease'}`}>
        {isHealthy ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} />
            Plant appears healthy
          </span>
        ) : (
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={16} />
            Disease detected
          </span>
        )}
      </div>
    </div>
  );
};

export default ResultCard;

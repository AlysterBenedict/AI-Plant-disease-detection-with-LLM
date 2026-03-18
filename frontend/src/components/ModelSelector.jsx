import React, { useEffect, useState } from 'react';
import { Cpu } from 'lucide-react';
import axios from 'axios';

const ModelSelector = ({ selectedModel, onModelChange }) => {
  const [models, setModels] = useState([]);

  useEffect(() => {
    axios
      .get('http://localhost:8000/models')
      .then((res) => setModels(res.data.models))
      .catch(() => {
        // Fallback defaults if backend is unreachable
        setModels([
          { id: 'tensorflow', name: 'TensorFlow (Keras)', description: 'Custom CNN · ~89% accuracy' },
          { id: 'pytorch', name: 'PyTorch (Base)', description: 'EfficientNetV2-S · 89.5% accuracy' },
          { id: 'pytorch_sota', name: 'PyTorch (SOTA)', description: 'EfficientNetV2-S Fine-Tuned · 99.6% accuracy' },
        ]);
      });
  }, []);

  return (
    <div className="model-selector animate-fade-in" style={{ animationDelay: '0.15s' }}>
      <div className="model-selector-header">
        <div className="model-icon-wrap">
          <Cpu size={20} />
        </div>
        <span className="model-selector-label">Select Model</span>
      </div>

      <div className="model-options">
        {models.map((m) => (
          <button
            key={m.id}
            className={`model-option ${selectedModel === m.id ? 'active' : ''}`}
            onClick={() => onModelChange(m.id)}
          >
            <span className="model-option-name">{m.name}</span>
            <span className="model-option-desc">{m.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ModelSelector;

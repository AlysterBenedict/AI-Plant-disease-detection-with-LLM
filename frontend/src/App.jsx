import React, { useState } from 'react';
import axios from 'axios';
import { Leaf } from 'lucide-react';
import ImageUploader from './components/ImageUploader';
import ResultCard from './components/ResultCard';
import AIFeedbackCard from './components/AIFeedbackCard';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setResult(null);
    setError(null);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:8000/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
    } catch (err) {
      console.error('Error analyzing image:', err);
      setError('Failed to analyze the image. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetAnalysis = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
  };

  return (
    <>
      {/* Animated liquid background blobs */}
      <div className="bg-blobs">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
      </div>

      <div className="app-container">
        <header className="header animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="header-icon-wrap">
            <Leaf size={44} />
          </div>
          <h1>PlantScan AI</h1>
          <p>Instantly detect and diagnose plant diseases with high accuracy</p>
        </header>

        <main className={`main-content ${result ? 'has-result' : ''} ${result?.ai_feedback ? 'has-ai' : ''}`}>
          <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <ImageUploader
              onFileSelect={handleFileSelect}
              previewUrl={previewUrl}
              isLoading={isLoading}
              onAnalyze={handleAnalyze}
              onReset={resetAnalysis}
              hasResult={!!result}
            />
          </div>

          {result && (
            <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.3s', animationFillMode: 'both' }}>
              <ResultCard result={result} />
            </div>
          )}
              
          {result?.ai_feedback && (
            <AIFeedbackCard feedback={result.ai_feedback.feedback} />
          )}

          {error && (
            <div className="glass-panel error-panel animate-fade-in" style={{ animationDelay: '0.3s', animationFillMode: 'both', marginTop: '2rem' }}>
              <p>{error}</p>
            </div>
          )}
        </main>

        <footer className="footer">
          Powered by AI · PlantScan
        </footer>
      </div>
    </>
  );
}

export default App;

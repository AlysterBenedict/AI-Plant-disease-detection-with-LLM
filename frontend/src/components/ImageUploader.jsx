import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X } from 'lucide-react';

const ImageUploader = ({ onFileSelect, previewUrl, isLoading, onAnalyze, onReset, hasResult }) => {
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.type.match('image.*')) {
      alert('Please select an image file');
      return;
    }
    onFileSelect(file);
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="upload-container">
      {!previewUrl ? (
        <div
          className={`upload-area ${isDragActive ? 'active' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={onButtonClick}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleChange}
            style={{ display: 'none' }}
          />
          <UploadCloud size={64} className="upload-icon" />
          <div className="upload-text">
            <h3>Drag & Drop</h3>
            <p>or click to select a plant leaf image</p>
          </div>
        </div>
      ) : (
        <div className="image-preview-container animate-fade-in">
          <div className="image-preview-wrapper">
            <img src={previewUrl} alt="Preview" className="image-preview" />
            {!isLoading && !hasResult && (
              <button className="close-btn" onClick={onReset}>
                <X size={16} />
              </button>
            )}
          </div>

          {!hasResult ? (
            <button
              className={`btn ${!isLoading ? 'btn-pulse' : ''}`}
              onClick={onAnalyze}
              disabled={isLoading}
              style={{ width: '100%' }}
            >
              {isLoading ? (
                <>
                  <div className="loader"></div>
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <ImageIcon size={20} />
                  <span>Analyze Plant</span>
                </>
              )}
            </button>
          ) : (
            <button
              className="btn btn-secondary"
              onClick={onReset}
              style={{ width: '100%' }}
            >
              <span>Scan Another Plant</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ImageUploader;

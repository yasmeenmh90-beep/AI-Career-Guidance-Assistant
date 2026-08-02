import { useState, useRef } from 'react';
import { Upload, FileText, Loader2, Download } from 'lucide-react';

export default function Resume() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('resume_file', file);

    try {
      const response = await fetch('/api/resume/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="mb-6 text-center">
        <h1>Resume Review</h1>
        <p className="text-secondary">Upload your PDF or DOCX resume to get actionable, AI-powered feedback.</p>
      </div>

      {!result && (
        <div className="upload-container surface-panel">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx"
            style={{ display: 'none' }}
          />
          
          <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
            <Upload size={48} className="upload-icon mb-4" />
            <h3>{file ? file.name : "Drag & drop or click to upload"}</h3>
            <p className="text-muted mt-2">Supports .pdf and .docx</p>
          </div>

          <button 
            className="btn-primary mt-6" 
            style={{ width: '100%' }}
            onClick={handleUpload}
            disabled={!file || loading}
          >
            {loading ? (
              <><Loader2 className="spin" size={20} /> Analyzing Resume...</>
            ) : (
              <><FileText size={20} /> Analyze Resume</>
            )}
          </button>

          {error && <div className="error-message mt-4">{error}</div>}
        </div>
      )}

      {result && (
        <div className="surface-panel animate-fade-in">
          <div className="flex-between mb-6">
            <h2>Feedback for {result.filename}</h2>
            <button className="btn-secondary" onClick={() => {
              setResult(null);
              setFile(null);
            }}>
              Upload Another
            </button>
          </div>
          
          <div className="markdown-content" dangerouslySetInnerHTML={{ __html: result.feedback_html }} />
        </div>
      )}
    </div>
  );
}

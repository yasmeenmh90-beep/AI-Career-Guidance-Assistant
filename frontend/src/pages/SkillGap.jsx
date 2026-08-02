import { useState, useEffect, useRef } from 'react';
import { Upload, Target, Loader2 } from 'lucide-react';

export default function SkillGap() {
  const [file, setFile] = useState(null);
  const [roles, setRoles] = useState([]);
  const [targetRole, setTargetRole] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetch('/api/careers/')
      .then(res => res.json())
      .then(data => {
        if (data.careers) {
          setRoles(data.careers);
        }
      })
      .catch(err => console.error("Failed to load careers", err));
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || !targetRole) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('resume_file', file);
    formData.append('target_role', targetRole);

    try {
      const response = await fetch('/api/skill-gap/', {
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
        <h1>Skill Gap Analysis</h1>
        <p className="text-secondary">Compare your resume to your dream role and get a custom learning plan.</p>
      </div>

      {!result && (
        <div className="upload-container surface-panel">
          <div className="mb-6">
            <label className="block mb-2 text-secondary">Select Target Role</label>
            <select 
              className="input-field" 
              value={targetRole} 
              onChange={e => setTargetRole(e.target.value)}
            >
              <option value="">-- Choose a Role --</option>
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx"
            style={{ display: 'none' }}
          />
          
          <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
            <Upload size={48} className="upload-icon mb-4" />
            <h3>{file ? file.name : "Upload Resume (PDF/DOCX)"}</h3>
          </div>

          <button 
            className="btn-primary mt-6" 
            style={{ width: '100%' }}
            onClick={handleUpload}
            disabled={!file || !targetRole || loading}
          >
            {loading ? (
              <><Loader2 className="spin" size={20} /> Analyzing Gap...</>
            ) : (
              <><Target size={20} /> Analyze Skill Gap</>
            )}
          </button>

          {error && <div className="error-message mt-4">{error}</div>}
        </div>
      )}

      {result && (
        <div className="surface-panel animate-fade-in">
          <div className="flex-between mb-6">
            <h2>Skill Gap for {result.target_role}</h2>
            <button className="btn-secondary" onClick={() => {
              setResult(null);
            }}>
              Start Over
            </button>
          </div>

          {result.missing_skills && result.missing_skills.length > 0 && (
            <div className="missing-skills-tags mb-6">
              <h4>Missing Skills to Focus On:</h4>
              <div className="tags-container mt-2">
                {result.missing_skills.map((skill, i) => (
                  <span key={i} className="skill-tag">{skill}</span>
                ))}
              </div>
            </div>
          )}
          
          <div className="markdown-content" dangerouslySetInnerHTML={{ __html: result.feedback_html }} />
        </div>
      )}
    </div>
  );
}

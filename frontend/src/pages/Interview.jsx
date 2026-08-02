import { useState, useEffect } from 'react';
import { Mic, Send, Loader2 } from 'lucide-react';

export default function Interview() {
  const [roles, setRoles] = useState([]);
  const [targetRole, setTargetRole] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [inProgress, setInProgress] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [progress, setProgress] = useState('');
  
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState(null);

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

  const handleStart = async () => {
    if (!targetRole) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/interview/start/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interview_role: targetRole }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      setInProgress(true);
      setCurrentQuestion(data.question);
      setProgress(data.progress);
      setAnswer('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async (e) => {
    e.preventDefault();
    if (!answer.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/interview/answer/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      if (data.is_final) {
        setInProgress(false);
        setResult(data);
      } else {
        setCurrentQuestion(data.question);
        setProgress(data.progress);
        setAnswer('');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="mb-6 text-center">
        <h1>Mock Interview Simulator</h1>
        <p className="text-secondary">Practice realistic interview questions tailored to your dream role.</p>
      </div>

      {!inProgress && !result && (
        <div className="upload-container surface-panel">
          <div className="mb-6">
            <label className="block mb-2 text-secondary">Select Role to Interview For</label>
            <select 
              className="input-field" 
              value={targetRole} 
              onChange={e => setTargetRole(e.target.value)}
            >
              <option value="">-- Choose a Role --</option>
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <button 
            className="btn-primary mt-4" 
            style={{ width: '100%' }}
            onClick={handleStart}
            disabled={!targetRole || loading}
          >
            {loading ? (
              <><Loader2 className="spin" size={20} /> Starting Interview...</>
            ) : (
              <><Mic size={20} /> Start Interview</>
            )}
          </button>

          {error && <div className="error-message mt-4">{error}</div>}
        </div>
      )}

      {inProgress && (
        <div className="surface-panel animate-fade-in max-w-3xl mx-auto">
          <div className="flex-between mb-4">
            <span className="text-accent text-sm font-semibold">{progress}</span>
            <span className="text-secondary text-sm">Role: {targetRole}</span>
          </div>
          
          <h2 className="mb-6">{currentQuestion}</h2>

          <form onSubmit={handleAnswerSubmit}>
            <textarea
              className="input-field mb-4"
              rows={5}
              placeholder="Type your answer here..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={loading}
              style={{ resize: 'vertical' }}
            />
            
            <button 
              type="submit"
              className="btn-primary"
              disabled={!answer.trim() || loading}
            >
              {loading ? (
                <><Loader2 className="spin" size={20} /> Submitting...</>
              ) : (
                <><Send size={20} /> Submit Answer</>
              )}
            </button>
          </form>

          {error && <div className="error-message mt-4">{error}</div>}
        </div>
      )}

      {result && (
        <div className="surface-panel animate-fade-in">
          <div className="flex-between mb-6">
            <h2>Interview Feedback Report</h2>
            <button className="btn-secondary" onClick={() => {
              setResult(null);
              setTargetRole('');
            }}>
              Practice Again
            </button>
          </div>
          
          <div className="markdown-content" dangerouslySetInnerHTML={{ __html: result.feedback_html }} />
        </div>
      )}
    </div>
  );
}

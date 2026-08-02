import { useState } from 'react';
import { Send, Loader2, Search } from 'lucide-react';

export default function Chat() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query }),
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
      <div className="mb-6">
        <h1>AI Career Advisor</h1>
        <p className="text-secondary">Ask any question about career paths, skills, or get personalized advice.</p>
      </div>

      <div className="surface-panel mb-6">
        <form onSubmit={handleSubmit} className="chat-form">
          <div className="search-wrapper">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              className="input-field chat-input"
              placeholder="e.g., How do I become a Data Scientist?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="btn-primary" disabled={loading || !query.trim()}>
              {loading ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
            </button>
          </div>
        </form>
        {error && <div className="error-message mt-4">{error}</div>}
      </div>

      {result && (
        <div className="surface-panel animate-fade-in results-panel">
          <div className="markdown-content" dangerouslySetInnerHTML={{ __html: result.answer_html }} />
          
          {result.matched_career && (
            <div className="matched-career-section mt-6">
              <h3>Target Roadmap: {result.matched_career}</h3>
              
              <div className="roadmap-grid mt-4">
                <div className="roadmap-column">
                  <h4>Steps to Follow</h4>
                  <ul className="custom-list">
                    {result.roadmap.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ul>
                </div>
                <div className="roadmap-column">
                  <h4>Recommended Courses</h4>
                  <ul className="custom-list">
                    {result.courses.map((course, i) => (
                      <li key={i}>
                        <a href={course.link} target="_blank" rel="noopener noreferrer">{course.name}</a>
                        <span className="platform-tag">{course.platform}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

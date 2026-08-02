import { useState, useEffect } from 'react';
import { Loader2, Download } from 'lucide-react';

export default function History() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/history/')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load history');
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex-center mt-12">
        <Loader2 className="spin" size={32} style={{ color: 'var(--blaze)' }} />
      </div>
    );
  }

  if (error) {
    return <div className="error-message mt-12">{error}</div>;
  }

  return (
    <div className="animate-fade-in">
      <h1 className="mb-2">Your trail so far</h1>
      <p className="text-secondary mb-6">Dashboard and activity history</p>

      <div className="dashboard-grid">
        {/* Overview Card */}
        <div className="surface-panel dashboard-card">
          <div className="card-header">Overview</div>
          <h2 className="card-title">Activity Breakdown</h2>
          
          {data.total_activity > 0 ? (
            <div className="donut-container">
              <div className="donut-chart">
                <svg viewBox="0 0 116 116" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                  <circle cx="58" cy="58" r="46" fill="none" stroke="var(--ink)" strokeWidth="12" strokeOpacity="0.05" />
                  {data.donut_segments.map((seg, i) => (
                    seg.count > 0 && (
                      <circle 
                        key={i} 
                        cx="58" 
                        cy="58" 
                        r="46"
                        fill="none"
                        strokeWidth="12"
                        strokeLinecap="round"
                        style={{ 
                          stroke: seg.color, 
                          strokeDasharray: seg.dasharray, 
                          strokeDashoffset: seg.dashoffset,
                          transition: 'all 1s ease-out'
                        }}
                      />
                    )
                  ))}
                </svg>
                <div className="donut-center">
                  <span style={{ fontSize: '1.875rem', fontWeight: 'bold', fontFamily: 'var(--font-display)' }}>{data.total_activity}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--ink-soft)', fontWeight: 'bold', textTransform: 'uppercase' }}>Total</span>
                </div>
              </div>
              
              <div className="donut-legend">
                {data.donut_segments.map((seg, i) => (
                  <div key={i} className="legend-item">
                    <span className="legend-color" style={{ background: seg.color }}></span>
                    <span style={{ fontWeight: '500', flex: 1 }}>{seg.label}</span>
                    <span style={{ fontWeight: 'bold' }}>{seg.count}</span>
                    <span style={{ color: 'var(--ink-soft)', fontSize: '0.75rem', width: '2rem', textAlign: 'right' }}>{seg.percent}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-secondary" style={{ fontStyle: 'italic', marginTop: 'auto', marginBottom: 'auto' }}>Ask a question, check a resume, or start an interview to see your activity here.</p>
          )}
        </div>

        {/* Skill Trend Card */}
        <div className="surface-panel dashboard-card">
          <div className="card-header">Trend</div>
          <h2 className="card-title">Skill Gap Trends</h2>
          
          {data.skill_trend_rows && data.skill_trend_rows.length > 0 ? (
            <div className="trend-list">
              {data.skill_trend_rows.map((row, i) => (
                <div key={i} className="trend-item">
                  <span className="trend-rank" style={{ background: i === 0 ? 'var(--blaze)' : 'var(--pine)' }}>
                    {row.rank}
                  </span>
                  <span style={{ fontWeight: '500', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.label}</span>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    {row.dots.map(d => <span key={`d-${d}`} style={{ width: '0.5rem', height: '0.5rem', borderRadius: '50%', background: i === 0 ? 'var(--blaze)' : 'var(--pine)' }}></span>)}
                    {row.empty_dots.map(d => <span key={`e-${d}`} style={{ width: '0.5rem', height: '0.5rem', borderRadius: '50%', background: i === 0 ? 'var(--blaze)' : 'var(--pine)', opacity: 0.2 }}></span>)}
                  </div>
                  <span style={{ fontWeight: 'bold', color: 'var(--ink-soft)', fontSize: '0.75rem', width: '1.5rem', textAlign: 'right' }}>×{row.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary" style={{ fontStyle: 'italic', marginTop: 'auto', marginBottom: 'auto' }}>Run a skill-gap analysis to start seeing which skills come up most often.</p>
          )}
        </div>
      </div>

      <div>
        <div className="history-section">
          <h3 className="history-header"><span style={{ color: 'var(--blaze)' }}>💬</span> Questions Asked</h3>
          <div className="history-list">
            {data.chat_questions && data.chat_questions.length > 0 ? (
              data.chat_questions.map((q, i) => (
                <div key={i} className="history-item">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)', marginBottom: '0.25rem', fontFamily: 'var(--font-mono)' }}>{q.created_at}{q.matched_career ? ` • ${q.matched_career}` : ''}</div>
                    <div style={{ fontWeight: '500' }}>{q.question}</div>
                  </div>
                </div>
              ))
            ) : <p className="text-secondary" style={{ fontStyle: 'italic', fontSize: '0.875rem' }}>No questions asked yet.</p>}
          </div>
        </div>

        <div className="history-section">
          <h3 className="history-header"><span style={{ color: 'var(--focus)' }}>📄</span> Resume Checks</h3>
          <div className="history-list">
            {data.resume_reports && data.resume_reports.length > 0 ? (
              data.resume_reports.map((r, i) => (
                <div key={i} className="history-item">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)', marginBottom: '0.25rem', fontFamily: 'var(--font-mono)' }}>{r.created_at}</div>
                    <div style={{ fontWeight: '500' }}>{r.filename}</div>
                  </div>
                  <a href={`/history/resume/${r.id}/pdf/`} className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>
                    <Download size={14} /> PDF
                  </a>
                </div>
              ))
            ) : <p className="text-secondary" style={{ fontStyle: 'italic', fontSize: '0.875rem' }}>No resumes analyzed yet.</p>}
          </div>
        </div>

        <div className="history-section">
          <h3 className="history-header"><span style={{ color: 'var(--pine)' }}>🧭</span> Skill Gap Reports</h3>
          <div className="history-list">
            {data.skill_gap_reports && data.skill_gap_reports.length > 0 ? (
              data.skill_gap_reports.map((s, i) => (
                <div key={i} className="history-item">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)', marginBottom: '0.25rem', fontFamily: 'var(--font-mono)' }}>{s.created_at}</div>
                    <div style={{ fontWeight: '500' }}>{s.target_role}</div>
                  </div>
                  <a href={`/history/skill-gap/${s.id}/pdf/`} className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>
                    <Download size={14} /> PDF
                  </a>
                </div>
              ))
            ) : <p className="text-secondary" style={{ fontStyle: 'italic', fontSize: '0.875rem' }}>No skill gap reports yet.</p>}
          </div>
        </div>

        <div className="history-section">
          <h3 className="history-header"><span style={{ color: 'var(--moss)' }}>🎤</span> Mock Interviews</h3>
          <div className="history-list">
            {data.interview_reports && data.interview_reports.length > 0 ? (
              data.interview_reports.map((inv, i) => (
                <div key={i} className="history-item">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--ink-soft)', marginBottom: '0.25rem', fontFamily: 'var(--font-mono)' }}>{inv.created_at}</div>
                    <div style={{ fontWeight: '500' }}>{inv.role}</div>
                  </div>
                  <a href={`/history/interview/${inv.id}/pdf/`} className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>
                    <Download size={14} /> PDF
                  </a>
                </div>
              ))
            ) : <p className="text-secondary" style={{ fontStyle: 'italic', fontSize: '0.875rem' }}>No mock interviews completed yet.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

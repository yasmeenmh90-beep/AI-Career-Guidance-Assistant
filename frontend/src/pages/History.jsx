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
    <div className="animate-fade-in max-w-3xl mx-auto pb-12">
      <div className="mb-8">
        <h1>Your trail so far</h1>
        <p className="text-secondary">Dashboard and activity history</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        {/* Overview Chart */}
        <div className="surface-panel h-full flex flex-col">
          <span className="text-secondary text-sm font-bold uppercase tracking-wider mb-2">Overview</span>
          <h2 className="mb-6 text-xl">📊 Activity Breakdown</h2>
          
          {data.total_activity > 0 ? (
            <div className="flex items-center gap-6 mt-auto mb-auto">
              <div className="relative w-32 h-32 flex-shrink-0">
                <svg viewBox="0 0 116 116" className="w-full h-full -rotate-90">
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
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold font-display">{data.total_activity}</span>
                  <span className="text-xs text-secondary font-bold uppercase">Total</span>
                </div>
              </div>
              
              <div className="flex flex-col gap-3 flex-1">
                {data.donut_segments.map((seg, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: seg.color }}></span>
                    <span className="font-medium flex-1">{seg.label}</span>
                    <span className="font-bold">{seg.count}</span>
                    <span className="text-secondary text-xs w-8 text-right">{seg.percent}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-secondary italic mt-auto mb-auto">Ask a question, check a resume, or start an interview to see your activity here.</p>
          )}
        </div>

        {/* Skill Trend */}
        <div className="surface-panel h-full flex flex-col">
          <span className="text-secondary text-sm font-bold uppercase tracking-wider mb-2">Trend</span>
          <h2 className="mb-6 text-xl">🧭 Skill Gap Trends</h2>
          
          {data.skill_trend_rows && data.skill_trend_rows.length > 0 ? (
            <div className="flex flex-col gap-4 mt-auto mb-auto">
              {data.skill_trend_rows.map((row, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span className="w-5 h-5 flex items-center justify-center rounded bg-ink text-white font-bold text-xs flex-shrink-0" style={{ background: i === 0 ? 'var(--blaze)' : 'var(--pine)' }}>
                    {row.rank}
                  </span>
                  <span className="font-medium flex-1 truncate">{row.label}</span>
                  <div className="flex gap-1">
                    {row.dots.map(d => <span key={`d-${d}`} className="w-2 h-2 rounded-full" style={{ background: i === 0 ? 'var(--blaze)' : 'var(--pine)' }}></span>)}
                    {row.empty_dots.map(d => <span key={`e-${d}`} className="w-2 h-2 rounded-full opacity-20" style={{ background: i === 0 ? 'var(--blaze)' : 'var(--pine)' }}></span>)}
                  </div>
                  <span className="font-bold text-secondary text-xs w-6 text-right">×{row.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary italic mt-auto mb-auto">Run a skill-gap analysis to start seeing which skills come up most often.</p>
          )}
        </div>
      </div>

      <div className="space-y-8">
        <div>
          <h3 className="mb-4 flex items-center gap-2 border-b border-ink border-opacity-10 pb-2"><span className="text-blaze">💬</span> Questions Asked</h3>
          <div className="space-y-3">
            {data.chat_questions && data.chat_questions.length > 0 ? (
              data.chat_questions.map((q, i) => (
                <div key={i} className="bg-ink bg-opacity-5 p-4 rounded-lg">
                  <div className="text-xs text-secondary mb-1 font-mono">{q.created_at}{q.matched_career ? ` — ${q.matched_career}` : ''}</div>
                  <div className="font-medium">{q.question}</div>
                </div>
              ))
            ) : <p className="text-secondary italic text-sm">No questions asked yet.</p>}
          </div>
        </div>

        <div>
          <h3 className="mb-4 flex items-center gap-2 border-b border-ink border-opacity-10 pb-2"><span className="text-focus">📋</span> Resume Checks</h3>
          <div className="space-y-3">
            {data.resume_reports && data.resume_reports.length > 0 ? (
              data.resume_reports.map((r, i) => (
                <div key={i} className="bg-ink bg-opacity-5 p-4 rounded-lg flex items-center justify-between gap-4">
                  <div>
                    <div className="text-xs text-secondary mb-1 font-mono">{r.created_at}</div>
                    <div className="font-medium">{r.filename}</div>
                  </div>
                  <a href={`/history/resume/${r.id}/pdf/`} className="btn-secondary py-1 px-3 text-xs flex items-center gap-1">
                    <Download size={14} /> PDF
                  </a>
                </div>
              ))
            ) : <p className="text-secondary italic text-sm">No resumes analyzed yet.</p>}
          </div>
        </div>

        <div>
          <h3 className="mb-4 flex items-center gap-2 border-b border-ink border-opacity-10 pb-2"><span className="text-pine">🧭</span> Skill Gap Reports</h3>
          <div className="space-y-3">
            {data.skill_gap_reports && data.skill_gap_reports.length > 0 ? (
              data.skill_gap_reports.map((s, i) => (
                <div key={i} className="bg-ink bg-opacity-5 p-4 rounded-lg flex items-center justify-between gap-4">
                  <div>
                    <div className="text-xs text-secondary mb-1 font-mono">{s.created_at}</div>
                    <div className="font-medium">{s.target_role}</div>
                  </div>
                  <a href={`/history/skill-gap/${s.id}/pdf/`} className="btn-secondary py-1 px-3 text-xs flex items-center gap-1">
                    <Download size={14} /> PDF
                  </a>
                </div>
              ))
            ) : <p className="text-secondary italic text-sm">No skill gap reports yet.</p>}
          </div>
        </div>

        <div>
          <h3 className="mb-4 flex items-center gap-2 border-b border-ink border-opacity-10 pb-2"><span className="text-moss">🎤</span> Mock Interviews</h3>
          <div className="space-y-3">
            {data.interview_reports && data.interview_reports.length > 0 ? (
              data.interview_reports.map((inv, i) => (
                <div key={i} className="bg-ink bg-opacity-5 p-4 rounded-lg flex items-center justify-between gap-4">
                  <div>
                    <div className="text-xs text-secondary mb-1 font-mono">{inv.created_at}</div>
                    <div className="font-medium">{inv.role}</div>
                  </div>
                  <a href={`/history/interview/${inv.id}/pdf/`} className="btn-secondary py-1 px-3 text-xs flex items-center gap-1">
                    <Download size={14} /> PDF
                  </a>
                </div>
              ))
            ) : <p className="text-secondary italic text-sm">No mock interviews completed yet.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

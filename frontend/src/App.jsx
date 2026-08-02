import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { Compass, MessageSquare, FileText, Target, Mic, LogOut, User } from 'lucide-react';
import { useState, useEffect } from 'react';
import Home from './pages/Home';
import Chat from './pages/Chat';
import Resume from './pages/Resume';
import SkillGap from './pages/SkillGap';
import History from './pages/History';
import Interview from './pages/Interview';
import Login from './pages/Login';

function Navigation({ user, onLogout }) {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout/', { method: 'POST' });
      onLogout();
      navigate('/login');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <nav className="topbar">
      <Link to="/" style={{ color: 'var(--ink)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', fontSize: '1.2rem' }}>
        <Compass size={24} style={{ color: 'var(--blaze)' }} />
        Trailmark
      </Link>
      <div className="nav-links">
        {user ? (
          <>
            <Link to="/history" className="nav-link" style={{ marginRight: '1rem', fontWeight: 'bold' }}>Dashboard</Link>
            <Link to="/chat" className="nav-link">Advisor</Link>
            <Link to="/resume" className="nav-link">Resume</Link>
            <Link to="/skill-gap" className="nav-link">Skill Gap</Link>
            <Link to="/interview" className="nav-link">Mock Interview</Link>
            <div className="flex items-center gap-4 ml-4 pl-4 border-l border-ink border-opacity-20">
              <span className="text-sm font-bold flex items-center gap-1"><User size={14}/> {user}</span>
              <button onClick={handleLogout} className="btn-secondary py-1 px-3 text-xs flex items-center gap-1">
                <LogOut size={14}/> Logout
              </button>
            </div>
          </>
        ) : (
          <Link to="/login" className="btn-primary py-1 px-4 text-sm">Sign In</Link>
        )}
      </div>
    </nav>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/status/')
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setUser(data.user);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex-center h-screen"><Compass className="spin" size={32} style={{color: 'var(--blaze)'}} /></div>;
  }

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navigation user={user} onLogout={() => setUser(null)} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login onLogin={(u) => setUser(u)} />} />
            <Route path="/history" element={<History />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/resume" element={<Resume />} />
            <Route path="/skill-gap" element={<SkillGap />} />
            <Route path="/interview" element={<Interview />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

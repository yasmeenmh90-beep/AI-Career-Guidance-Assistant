import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate, Navigate } from 'react-router-dom';
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

  // Don't show nav items on login page if not logged in
  if (!user && location.pathname === '/login') {
    return (
      <nav className="topbar" style={{ justifyContent: 'center' }}>
        <div style={{ color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', fontSize: '1.5rem' }}>
          <Compass size={28} style={{ color: 'var(--blaze)' }} />
          Trailmark
        </div>
      </nav>
    );
  }

  return (
    <nav className="topbar">
      <Link to="/" style={{ color: 'var(--ink)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', fontSize: '1.2rem' }}>
        <Compass size={24} style={{ color: 'var(--blaze)' }} />
        Trailmark
      </Link>
      <div className="nav-links">
        {user && (
          <>
            <Link to="/history" className="nav-link" style={{ marginRight: '1rem', fontWeight: 'bold' }}>Dashboard</Link>
            <Link to="/chat" className="nav-link">Advisor</Link>
            <Link to="/resume" className="nav-link">Resume</Link>
            <Link to="/skill-gap" className="nav-link">Skill Gap</Link>
            <Link to="/interview" className="nav-link">Mock Interview</Link>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginLeft: '1rem', paddingLeft: '1rem', borderLeft: '1px solid var(--line)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <User size={14}/> {user}
              </span>
              <button onClick={handleLogout} className="btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>
                <LogOut size={14}/> Logout
              </button>
            </div>
          </>
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
            <Route path="/login" element={user ? <Navigate to="/history" /> : <Login onLogin={(u) => setUser(u)} />} />
            <Route path="/" element={user ? <Home /> : <Navigate to="/login" />} />
            <Route path="/history" element={user ? <History /> : <Navigate to="/login" />} />
            <Route path="/chat" element={user ? <Chat /> : <Navigate to="/login" />} />
            <Route path="/resume" element={user ? <Resume /> : <Navigate to="/login" />} />
            <Route path="/skill-gap" element={user ? <SkillGap /> : <Navigate to="/login" />} />
            <Route path="/interview" element={user ? <Interview /> : <Navigate to="/login" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Compass, MessageSquare, FileText, Target, Mic } from 'lucide-react';
import Home from './pages/Home';
import Chat from './pages/Chat';
import Resume from './pages/Resume';
import SkillGap from './pages/SkillGap';
import Interview from './pages/Interview';

function Navigation() {
  const location = useLocation();

  return (
    <nav className="topbar">
      <Link to="/" style={{ color: 'var(--ink)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', fontSize: '1.2rem' }}>
        <Compass size={24} style={{ color: 'var(--blaze)' }} />
        Trailmark
      </Link>
      <div className="nav-links">
        <Link to="/chat" className="nav-link">Advisor</Link>
        <Link to="/resume" className="nav-link">Resume</Link>
        <Link to="/skill-gap" className="nav-link">Skill Gap</Link>
        <Link to="/interview" className="nav-link">Mock Interview</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
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

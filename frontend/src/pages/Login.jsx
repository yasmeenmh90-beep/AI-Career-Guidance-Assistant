import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

export default function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const endpoint = isLogin ? '/api/auth/login/' : '/api/auth/signup/';
    const body = isLogin ? { username, password } : { username, email, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      
      if (res.ok && data.success) {
        onLogin(data.user);
        navigate('/history');
      } else {
        setError(data.error || 'Authentication failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in flex items-center justify-center pt-12 pb-24">
      <div className="surface-panel w-full max-w-md">
        <h2 className="mb-2 text-2xl">{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
        <p className="text-secondary mb-6">
          {isLogin ? 'Sign in to view your career dashboard.' : 'Start your journey with Trailmark.'}
        </p>

        {error && <div className="error-message mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-bold uppercase tracking-wider mb-2">Username</label>
            <input 
              type="text" 
              required 
              className="chat-input" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
            />
          </div>

          {!isLogin && (
            <div>
              <label className="block text-sm font-bold uppercase tracking-wider mb-2">Email</label>
              <input 
                type="email" 
                required 
                className="chat-input" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-bold uppercase tracking-wider mb-2">Password</label>
            <input 
              type="password" 
              required 
              className="chat-input" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full mt-6 justify-center">
            {loading ? <Loader2 className="spin" size={20} /> : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-secondary">{isLogin ? "Don't have an account?" : "Already have an account?"}</span>
          {' '}
          <button 
            type="button"
            className="text-blaze font-bold hover:underline bg-transparent border-none cursor-pointer"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}

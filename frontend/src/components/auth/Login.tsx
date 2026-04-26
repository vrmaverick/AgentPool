import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../../services/api';
import { useStore } from '../../store/useStore';
import { Coins } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { setUser } = useStore();

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const res = await authApi.login({ email, password });
      localStorage.setItem('token', res.data.access_token);
      setUser({ id: res.data.user_id, email, name: email.split('@')[0] });
      navigate('/dashboard');
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1115]">
      <div className="bg-[#1a1d24] p-8 rounded-2xl border border-gray-800 w-full max-w-md">
        <div className="flex items-center justify-center gap-3 mb-8 text-3xl font-bold text-white tracking-wide">
          <Coins size={36} className="text-amber-500" />
          <span><span className="text-amber-500">Token</span>Lend</span>
        </div>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <input 
              type="email" 
              placeholder="Email" 
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full bg-[#0f1115] border border-gray-700 rounded-lg p-3 text-white focus:border-amber-500 focus:outline-none"
            />
          </div>
          <div>
            <input 
              type="password" 
              placeholder="Password" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full bg-[#0f1115] border border-gray-700 rounded-lg p-3 text-white focus:border-amber-500 focus:outline-none"
            />
          </div>
          <button type="submit" className="w-full bg-amber-500 text-amber-950 font-bold p-3 rounded-lg hover:bg-amber-400 mt-4">
            Login
          </button>
        </form>
      </div>
    </div>
  );
}

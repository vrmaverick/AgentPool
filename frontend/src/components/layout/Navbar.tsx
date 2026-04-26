
import { useStore } from '../../store/useStore';
import { LogOut, Coins } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const { user, wallet, setUser } = useStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/login');
  };

  return (
    <nav className="bg-[#1a1d24] border-b border-gray-800 px-6 py-4 flex justify-between items-center">
      <div className="flex items-center gap-2 text-xl font-bold text-white tracking-wide">
        <span className="text-amber-500">Token</span>Lend
      </div>
      
      {user && (
        <div className="flex items-center gap-6">
          <div className="bg-amber-500/10 text-amber-500 px-4 py-1.5 rounded-full flex items-center gap-2 border border-amber-500/20 font-medium">
            <Coins size={16} />
            <span>{wallet?.tlc_balance?.toFixed(2) || '0.00'} TLC</span>
          </div>
          
          <div className="text-gray-400 text-sm">{user.email}</div>
          
          <button 
            onClick={handleLogout}
            className="text-gray-400 hover:text-white transition-colors p-2"
          >
            <LogOut size={18} />
          </button>
        </div>
      )}
    </nav>
  );
}

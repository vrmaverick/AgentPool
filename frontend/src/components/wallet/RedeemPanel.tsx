import { useState } from 'react';
import { useStore } from '../../store/useStore';
import { walletApi } from '../../services/api';
import { X } from 'lucide-react';

export default function RedeemPanel({ isOpen, onClose, option }: { isOpen: boolean, onClose: () => void, option: any }) {
  const { agents, wallet } = useStore();
  const [amount, setAmount] = useState('');
  const [targetAgent, setTargetAgent] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  if (!isOpen || !option) return null;

  const handleRedeem = async () => {
    try {
      setLoading(true);
      setSuccessMsg('');
      await walletApi.redeem({
        type: option.type,
        tlc_amount: parseFloat(amount),
        agent_id: targetAgent
      });
      
      setSuccessMsg(`Successfully redeemed! Agents balance updated.`);
      setTimeout(() => {
        setSuccessMsg('');
        onClose();
        setAmount('');
        setTargetAgent('');
      }, 3000);
      
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Redemption failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-[#1a1d24] border border-gray-800 rounded-2xl w-full max-w-md p-6 relative shadow-2xl">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white">
          <X size={20} />
        </button>
        
        <h2 className="text-2xl font-bold text-white mb-2">Redeem TLC for {option.type}</h2>
        <p className="text-amber-500 font-medium mb-6 bg-amber-500/10 p-3 rounded-lg border border-amber-500/20">
          Rate: {option.rate}
        </p>
        
        {successMsg ? (
          <div className="bg-emerald-500/20 text-emerald-400 p-6 rounded-xl border border-emerald-500/30 text-center font-bold animate-pulse">
            {successMsg}
          </div>
        ) : (
          <div className="space-y-5">
            <div>
              <label className="block text-gray-400 text-sm mb-2">TLC Amount to Redeem</label>
              <input 
                type="number" 
                value={amount} 
                onChange={(e) => setAmount(e.target.value)}
                placeholder={`Min ${option.min} TLC`}
                className="w-full bg-[#0f1115] border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-amber-500"
              />
              <div className="text-xs text-gray-500 mt-1">Available: {wallet?.tlc_balance?.toFixed(2)} TLC</div>
            </div>
            
            <div>
              <label className="block text-gray-400 text-sm mb-2">Target Agent</label>
              <select 
                value={targetAgent}
                onChange={(e) => setTargetAgent(e.target.value)}
                className="w-full bg-[#0f1115] border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">Select an agent</option>
                {agents.map(a => (
                  <option key={a.id} value={a.id}>{a.name} ({a.role})</option>
                ))}
              </select>
            </div>
            
            <button 
              onClick={handleRedeem}
              disabled={loading || !amount || !targetAgent || parseFloat(amount) < option.min || parseFloat(amount) > (wallet?.tlc_balance || 0)}
              className="w-full bg-amber-500 text-amber-950 font-bold p-3 rounded-lg hover:bg-amber-400 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed mt-4"
            >
              {loading ? 'Processing...' : 'Confirm Redemption'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

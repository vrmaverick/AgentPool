import { useState } from 'react';
import { useStore } from '../../store/useStore';
import { Coins, Clock, Sparkles } from 'lucide-react';
import RedeemPanel from './RedeemPanel';

export default function TLCWalletCard() {
  const { wallet } = useStore();
  const [isRedeemOpen, setIsRedeemOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<any>(null);

  const handleOpenRedeem = (opt: any) => {
    if (opt.disabled) return;
    setSelectedOption(opt);
    setIsRedeemOpen(true);
  };

  return (
    <>
      <div className="bg-gradient-to-br from-amber-500/20 to-amber-900/20 border border-amber-500/30 rounded-2xl p-6 relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
        
        <div className="flex justify-between items-start relative z-10">
          <div>
            <div className="flex items-center gap-2 text-amber-500 mb-1">
              <Coins size={20} />
              <h2 className="font-bold tracking-wide uppercase text-sm">TLC Wallet</h2>
            </div>
            <div className="text-5xl font-black text-white mt-2">
              {wallet?.tlc_balance?.toFixed(2) || '0.00'}
            </div>
            <div className="text-amber-400/80 text-sm mt-2 flex items-center gap-1.5">
              <Clock size={14} />
              +{wallet?.pending_tlc?.toFixed(2) || '0.00'} pending from active loans
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-gray-400 text-sm mb-1">Total Earned All-Time</div>
            <div className="text-xl font-bold text-gray-200">{wallet?.total_earned?.toFixed(2) || '0.00'}</div>
          </div>
        </div>

        <div className="mt-6 mb-8 bg-amber-950/40 border border-amber-500/20 rounded-lg p-3 flex items-center gap-3 relative z-10">
          <Sparkles size={16} className="text-amber-400" />
          <span className="text-amber-200/90 text-sm">Your idle tokens are earning TLC passively by being loaned to pipeline agents.</span>
        </div>

        <div className="flex gap-3 relative z-10">
          {wallet?.redemption_options?.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleOpenRedeem(opt)}
              disabled={opt.disabled}
              className={`flex-1 py-3 px-4 rounded-xl font-semibold transition-all ${
                opt.disabled 
                  ? 'bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-700' 
                  : i === 0 
                    ? 'bg-amber-500 text-amber-950 hover:bg-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.3)]'
                    : 'bg-[#1a1d24] text-amber-500 border border-amber-500/30 hover:bg-amber-500/10'
              }`}
            >
              {opt.type === 'tokens' ? 'Redeem for Tokens' : opt.type === 'trust' ? 'Boost Trust Score' : 'Cash Out (Coming Soon)'}
            </button>
          ))}
        </div>
      </div>

      <RedeemPanel 
        isOpen={isRedeemOpen} 
        onClose={() => setIsRedeemOpen(false)} 
        option={selectedOption} 
      />
    </>
  );
}

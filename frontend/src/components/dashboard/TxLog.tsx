
import { useStore } from '../../store/useStore';
import { ArrowRightLeft, PlusCircle, ShieldCheck } from 'lucide-react';

export default function TxLog() {
  const { wallet } = useStore();
  const txHistory = wallet?.history || [];

  return (
    <div className="bg-[#1a1d24] border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-bold text-white mb-4">Transaction History</h2>
      {txHistory.length === 0 ? (
        <div className="text-gray-500 text-center py-8">No transactions yet</div>
      ) : (
        <div className="space-y-3">
          {txHistory.map((tx) => (
            <div key={tx.id} className="flex items-center justify-between p-3 bg-[#22262f] rounded-lg">
              <div className="flex items-center gap-3">
                {tx.type.includes('trust') ? (
                  <ShieldCheck size={18} className="text-emerald-400" />
                ) : tx.type.includes('earned') ? (
                  <PlusCircle size={18} className="text-amber-400" />
                ) : (
                  <ArrowRightLeft size={18} className="text-blue-400" />
                )}
                <div>
                  <div className="text-gray-200 text-sm">{tx.description}</div>
                  <div className="text-gray-500 text-xs mt-1">
                    {new Date(tx.date).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-sm font-bold ${tx.amount > 0 ? 'text-amber-500' : 'text-gray-400'}`}>
                  {tx.amount > 0 ? '+' : ''}{tx.amount} TLC
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


import { useStore } from '../../store/useStore';
import { Activity, Coins, ShieldCheck, Zap } from 'lucide-react';

export default function StatsBar() {
  const { loans, agents, wallet } = useStore();
  
  const activeLoans = loans?.active?.length || 0;
  const totalLent = loans?.my_active_as_lender?.reduce((sum, l) => sum + l.amount, 0) || 0;
  const avgTrust = agents?.length ? (agents.reduce((sum, a) => sum + a.trust_score, 0) / agents.length).toFixed(2) : '0.00';
  const tlcEarned = wallet?.total_earned?.toFixed(2) || '0.00';

  const stats = [
    { label: 'Active Loans', value: activeLoans, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'Total Tokens Lent', value: totalLent, icon: Zap, color: 'text-purple-400', bg: 'bg-purple-400/10' },
    { label: 'TLC Earned', value: tlcEarned, icon: Coins, color: 'text-amber-500', bg: 'bg-amber-500/10', highlight: true },
    { label: 'Avg Trust Score', value: avgTrust, icon: ShieldCheck, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
  ];

  return (
    <div className="grid grid-cols-4 gap-4 mb-8">
      {stats.map((stat, i) => (
        <div key={i} className={`p-4 rounded-xl border ${stat.highlight ? 'border-amber-500/30 bg-amber-500/5' : 'border-gray-800 bg-[#1a1d24]'} flex items-center gap-4`}>
          <div className={`p-3 rounded-lg ${stat.bg} ${stat.color}`}>
            <stat.icon size={24} />
          </div>
          <div>
            <div className="text-gray-400 text-sm font-medium">{stat.label}</div>
            <div className={`text-2xl font-bold ${stat.highlight ? 'text-amber-500' : 'text-white'}`}>
              {stat.value}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

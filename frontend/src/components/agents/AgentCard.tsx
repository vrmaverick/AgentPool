import type { Agent } from '../../types';
import { Shield, Key, Database } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
}

export default function AgentCard({ agent }: AgentCardProps) {
  const pct = agent.max_balance > 0 ? (agent.token_balance / agent.max_balance) * 100 : 0;
  
  let barColor = 'bg-emerald-500';
  if (pct < 10) barColor = 'bg-red-500 animate-pulse';
  else if (pct < 50) barColor = 'bg-amber-500';

  return (
    <div className="bg-[#1a1d24] border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white font-semibold text-lg">{agent.name}</h3>
          <div className="text-xs text-gray-500 font-mono mt-1 flex items-center gap-1">
            <Key size={12} /> {agent.api_key_masked}
          </div>
        </div>
        <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
          agent.role === 'lender' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'
        }`}>
          {agent.role}
        </span>
      </div>

      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-gray-400 flex items-center gap-1"><Database size={14}/> Tokens</span>
            <span className="text-gray-200 font-medium">{agent.token_balance.toFixed(0)} / {agent.max_balance.toFixed(0)}</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
            <div className={`h-full ${barColor} transition-all duration-500`} style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
          </div>
        </div>

        <div className="flex justify-between items-center bg-[#22262f] p-2.5 rounded-lg border border-gray-800/50">
          <span className="text-gray-400 text-sm flex items-center gap-1"><Shield size={14} className="text-emerald-500"/> Trust Score</span>
          <span className="text-emerald-400 font-bold">{agent.trust_score.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

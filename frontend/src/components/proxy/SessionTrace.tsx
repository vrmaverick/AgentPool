import { useState } from 'react';
import { demoApi } from '../../services/api';
import { Play, ShieldCheck, Cpu } from 'lucide-react';

export default function SessionTrace() {
  const [events, setEvents] = useState<any[]>([]);
  const [activeStep, setActiveStep] = useState(0);

  const startDemo = async () => {
    setEvents([]);
    setActiveStep(0);
    try {
      await demoApi.seed();
      const response = await fetch('http://localhost:8000/demo/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));
            setEvents(prev => [...prev, data]);
            setActiveStep(data.step);
          }
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="bg-[#1a1d24] border border-gray-800 rounded-xl p-6 mt-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Cpu className="text-amber-500" />
          Live Session Trace
        </h2>
        <button 
          onClick={startDemo}
          className="bg-amber-500 hover:bg-amber-400 text-amber-950 font-bold px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Play size={18} />
          Run Hackathon Demo
        </button>
      </div>

      <div className="flex items-center justify-center gap-4 mb-8">
        {['ResearchAgent', 'SummaryAgent', 'ReportAgent'].map((box, i) => {
          let state = 'idle';
          if (activeStep >= 1 && i === 0) state = 'active';
          if (activeStep >= 4 && activeStep < 6 && i === 0) state = 'crisis';
          if (activeStep >= 9) state = 'done';

          return (
            <div key={i} className="flex items-center gap-4">
              <div className={`p-4 rounded-xl border-2 transition-all duration-500 ${
                state === 'crisis' ? 'border-red-500 bg-red-500/20 animate-pulse' :
                state === 'active' ? 'border-blue-500 bg-blue-500/20' :
                state === 'done' ? 'border-emerald-500 bg-emerald-500/20' :
                'border-gray-700 bg-gray-800'
              }`}>
                <div className="text-white font-bold">{box}</div>
                <div className="text-xs text-gray-400 mt-1 uppercase tracking-widest">{state}</div>
              </div>
              {i < 2 && <div className="w-8 h-0.5 bg-gray-700" />}
            </div>
          );
        })}
      </div>

      <div className="bg-[#0f1115] rounded-xl overflow-hidden border border-gray-800">
        <table className="w-full text-left">
          <thead className="bg-[#22262f] border-b border-gray-800 text-gray-400 text-sm">
            <tr>
              <th className="p-3">Step</th>
              <th className="p-3">Action</th>
              <th className="p-3">Detail</th>
              <th className="p-3">Tokens / TLC</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {events.map((ev, i) => (
              <tr key={i} className={`border-b border-gray-800/50 transition-colors ${
                ev.label.includes('Proxy') ? 'bg-amber-500/10' : 
                ev.label === 'TOKEN CRISIS' ? 'bg-red-500/10' : 'hover:bg-[#22262f]'
              }`}>
                <td className="p-3 text-gray-500">{ev.step}</td>
                <td className="p-3 text-white font-medium">{ev.label}</td>
                <td className="p-3 text-gray-300">{ev.detail}</td>
                <td className="p-3">
                  {ev.state?.tlc_yield_pending && <span className="text-amber-500 font-bold">+{ev.state.tlc_yield_pending} TLC Yield</span>}
                  {ev.state?.tokens && <span className="text-blue-400 font-mono">{ev.state.tokens} tkns</span>}
                  {ev.state?.key_used && <span className="text-gray-500 text-xs ml-2">via {ev.state.key_used}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activeStep >= 11 && (
        <div className="mt-8 p-6 bg-gradient-to-r from-amber-500/20 to-amber-900/20 border border-amber-500/40 rounded-xl flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-amber-500/20 rounded-full text-amber-500">
              <ShieldCheck size={24} />
            </div>
            <div>
              <h3 className="text-amber-500 font-bold text-lg">Priya earned 10 TLC!</h3>
              <p className="text-amber-200/80 text-sm">Redeemable for Groq tokens, trust boosts, or future cash outs.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import StatsBar from './components/dashboard/StatsBar';
import AgentCard from './components/agents/AgentCard';
import TxLog from './components/dashboard/TxLog';
import TLCWalletCard from './components/wallet/TLCWalletCard';
import SessionTrace from './components/proxy/SessionTrace';
import Login from './components/auth/Login';
import { usePolling } from './hooks/usePolling';
import { useStore } from './store/useStore';

function Dashboard() {
  usePolling();
  const { agents } = useStore();

  return (
    <div className="min-h-screen bg-[#0f1115]">
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-8">
        <StatsBar />
        
        <div className="mb-8">
          <TLCWalletCard />
        </div>
        
        <div className="mb-8">
          <SessionTrace />
        </div>
        
        <div className="grid grid-cols-3 gap-8">
          <div className="col-span-2">
            <h2 className="text-xl font-bold text-white mb-4">My Agents</h2>
            <div className="grid grid-cols-2 gap-4">
              {agents.map(agent => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
            {agents.length === 0 && (
              <div className="text-gray-500 p-8 border border-gray-800 rounded-xl text-center border-dashed">
                No agents registered yet.
              </div>
            )}
          </div>
          <div className="col-span-1">
            <TxLog />
          </div>
        </div>
      </main>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useStore();
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </Router>
  );
}

import { useEffect } from 'react';
import { agentApi, loanApi, walletApi } from '../services/api';
import { useStore } from '../store/useStore';

export function usePolling() {
  const { setAgents, setLoans, setWallet, user } = useStore();

  useEffect(() => {
    if (!user) return;
    
    const poll = async () => {
      try {
        const [agentsRes, loansRes, walletRes] = await Promise.all([
          agentApi.getAgents(),
          loanApi.getLoans(),
          walletApi.getWallet()
        ]);
        setAgents(agentsRes.data);
        setLoans(loansRes.data);
        setWallet(walletRes.data);
      } catch (err) {
        console.error("Polling error", err);
      }
    };

    poll(); // Initial poll
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [user, setAgents, setLoans, setWallet]);
}

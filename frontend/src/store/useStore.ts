import { create } from 'zustand';
import type { User, Agent, Loan, TLCWallet, TxRecord } from '../types';

interface StoreState {
  user: User | null;
  agents: Agent[];
  loans: { active: Loan[], history: Loan[], my_active_as_lender: Loan[], my_active_as_borrower: Loan[] };
  wallet: TLCWallet | null;
  txLog: TxRecord[];
  
  setUser: (user: User | null) => void;
  setAgents: (agents: Agent[]) => void;
  setLoans: (loans: any) => void;
  setWallet: (wallet: TLCWallet | null) => void;
  setTxLog: (txLog: TxRecord[]) => void;
}

export const useStore = create<StoreState>((set) => ({
  user: null,
  agents: [],
  loans: { active: [], history: [], my_active_as_lender: [], my_active_as_borrower: [] },
  wallet: null,
  txLog: [],
  
  setUser: (user) => set({ user }),
  setAgents: (agents) => set({ agents }),
  setLoans: (loans) => set({ loans }),
  setWallet: (wallet) => set({ wallet }),
  setTxLog: (txLog) => set({ txLog })
}));

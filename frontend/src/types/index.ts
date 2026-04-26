export interface User {
  id: string;
  name: string;
  email: string;
}

export interface Agent {
  id: string;
  name: string;
  role: 'pipeline' | 'lender';
  api_key_masked: string;
  token_balance: number;
  max_balance: number;
  trust_score: number;
  last_active?: string;
}

export interface Loan {
  id: string;
  lender_agent_id: string;
  borrower_agent_id: string;
  amount: number;
  tlc_yield_amount: number;
  status: string;
  due_time: string;
}

export interface TLCTransaction {
  id: string;
  date: string;
  type: string;
  amount: number;
  description: string;
  loan_id?: string;
}

export interface RedeemOption {
  type: 'tokens' | 'trust' | 'cashout';
  rate: string;
  min: number;
  disabled?: boolean;
}

export interface TLCWallet {
  tlc_balance: number;
  total_earned: number;
  total_redeemed: number;
  pending_tlc: number;
  redemption_options: RedeemOption[];
  history: TLCTransaction[];
}

export interface TxRecord {
  id: string;
  event_type: string;
  description: string;
  created_at: string;
}

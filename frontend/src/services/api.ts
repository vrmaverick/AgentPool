import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (data: any) => api.post('/user/login', data),
  register: (data: any) => api.post('/user/register', data)
};

export const agentApi = {
  getAgents: () => api.get('/agent'),
  registerAgent: (data: any) => api.post('/agent/register', data),
  useTokens: (data: any) => api.post('/agent/use_tokens', data)
};

export const loanApi = {
  getLoans: () => api.get('/loan'),
  requestLoan: (data: any) => api.post('/loan/request', data),
  repayLoan: (loanId: string) => api.post(`/loan/repay/${loanId}`)
};

export const walletApi = {
  getWallet: () => api.get('/wallet'),
  redeem: (data: any) => api.post('/wallet/redeem', data)
};

export const demoApi = {
  seed: () => api.post('/demo/seed'),
  run: () => api.post('/demo/run'),
  state: () => api.get('/demo/state')
};

export default api;

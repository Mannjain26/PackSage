import api from './api';

export const getDashboardStats = async () => {
  const { data } = await api.get('/dashboard/stats');
  return data;
};

export const getRecentScenarios = async () => {
  const { data } = await api.get('/dashboard/recent-scenarios');
  return data;
};

export const getAuditLog = async () => {
  const { data } = await api.get('/dashboard/audit');
  return data;
};

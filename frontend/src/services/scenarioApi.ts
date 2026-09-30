import api from './api';

export const getScenarios = async (params?: { status?: string; search?: string }) => {
  const { data } = await api.get('/scenarios', { params });
  return data;
};

export const getScenario = async (id: string) => {
  const { data } = await api.get(`/scenarios/${id}`);
  return data;
};

export const createScenario = async (payload: object) => {
  const { data } = await api.post('/scenarios', payload);
  return data;
};

export const updateScenario = async (id: string, payload: object) => {
  const { data } = await api.put(`/scenarios/${id}`, payload);
  return data;
};

export const generateRecommendations = async (id: string) => {
  const { data } = await api.post(`/scenarios/${id}/generate`);
  return data;
};

export const getScenarioRecommendations = async (id: string, priority?: string) => {
  const { data } = await api.get(`/scenarios/${id}/recommendations`, {
    params: priority ? { priority } : undefined
  });
  return data;
};

export const updateScenarioPriority = async (id: string, cost_priority: string) => {
  const { data } = await api.patch(`/scenarios/${id}/priority`, { cost_priority });
  return data;
};

export const getCostFormats = async () => {
  const { data } = await api.get('/cost/formats');
  return data;
};

export const estimateCost = async (payload: object) => {
  const { data } = await api.post('/cost/estimate', payload);
  return data;
};

export const deleteScenario = async (id: string) => {
  const { data } = await api.delete(`/scenarios/${id}`);
  return data;
};


import api from './api';

export const getMaterials = async (params?: object) => {
  const { data } = await api.get('/materials', { params });
  return data;
};

export const getMaterial = async (id: string) => {
  const { data } = await api.get(`/materials/${id}`);
  return data;
};

export const createMaterial = async (payload: object) => {
  const { data } = await api.post('/materials', payload);
  return data;
};

export const updateMaterial = async (id: string, payload: object) => {
  const { data } = await api.put(`/materials/${id}`, payload);
  return data;
};

export const verifyMaterial = async (id: string) => {
  const { data } = await api.post(`/materials/${id}/verify`);
  return data;
};

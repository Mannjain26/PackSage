import api from './api';

export interface InverseSolvePayload {
  commodity_category: string;
  target_shelf_life_days: number;
  pack_weight_grams?: number;
  pack_area_m2?: number;
  initial_moisture_pct?: number;
  critical_moisture_pct?: number;
  isotherm_slope?: number;
  fat_pct?: number;
  allowable_o2_uptake_ml_per_kg?: number;
  respiration_rate_mg_co2?: number;
  city_name?: string;
  season?: string;
  transit_mode?: string;
  cold_chain_break_hours?: number;
  break_temp_c?: number;
}

export const getClimateOptions = async () => {
  const { data } = await api.get('/solver/climate-options');
  return data;
};

export const solveInverseRequirements = async (payload: InverseSolvePayload) => {
  const { data } = await api.post('/solver/solve', payload);
  return data;
};

export const simulateDowngrade = async (payload: {
  original_shelf_life_days: number;
  current_cost_index: number;
  target_cost_index: number;
  commodity_category: string;
}) => {
  const { data } = await api.post('/solver/downgrade-simulation', payload);
  return data;
};

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import Layout from '../components/layout/Layout';
import { getScenarioRecommendations, generateRecommendations, updateScenarioPriority } from '../services/scenarioApi';
import api, { downloadReportFile } from '../services/api';
import { DisclaimerBanner, LoadingSkeleton, ErrorBox, EvidenceBadge } from '../components/ui/Shared';
import { 
  FileDown, ChevronDown, ChevronUp, Leaf, Package, FlaskConical, Wind, 
  CheckCircle2, XCircle, Droplets, ArrowLeft, ShieldCheck, DollarSign, 
  AlertTriangle, Award, Sparkles, Scale, TrendingDown
} from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, ZAxis } from 'recharts';

const PRIORITIES = [
  { id: 'balanced', label: 'Balanced Value', icon: Scale, desc: '60% Tech / 25% Cost / 15% Eco' },
  { id: 'cost_first', label: 'Lowest Cost First', icon: TrendingDown, desc: '40% Tech / 50% Cost / 10% Eco' },
  { id: 'performance_first', label: 'Best Performance', icon: Award, desc: '80% Tech / 10% Cost / 10% Eco' },
  { id: 'sustainability_first', label: 'Most Sustainable', icon: Leaf, desc: '45% Tech / 15% Cost / 40% Eco' },
];

const ScenarioResult: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [activePriority, setActivePriority] = useState<string>('balanced');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['recommendations', id, activePriority],
    queryFn: () => getScenarioRecommendations(id!, activePriority),
    enabled: !!id,
    retry: false
  });

  const generateMut = useMutation({
    mutationFn: () => generateRecommendations(id!),
    onSuccess: () => refetch(),
  });

  const priorityMut = useMutation({
    mutationFn: (prio: string) => updateScenarioPriority(id!, prio),
    onSuccess: () => {
      refetch();
    }
  });

  const generateReportMut = useMutation({
    mutationFn: async (recId: string) => {
      const { data } = await api.post(`/reports/generate/${recId}`);
      return data;
    },
    onSuccess: async (resData) => {
      try {
        await downloadReportFile(resData.report_id, `PackSage_Report_${resData.report_id}.pdf`);
      } catch (e) {
        console.error("Failed to download PDF", e);
      }
      navigate('/reports');
    }
  });

  const [selectedMaterials, setSelectedMaterials] = useState<Set<string>>(new Set());
  
  // Auto-select top 3 when data loads
  useEffect(() => {
    if (data && data.final_ranking && selectedMaterials.size === 0) {
      const top3 = data.final_ranking.slice(0, 3).map((m: any) => m.material_id);
      setSelectedMaterials(new Set(top3));
    }
    if (data?.selected_priority) {
      setActivePriority(data.selected_priority);
    } else if (data?.scenario?.cost_priority) {
      setActivePriority(data.scenario.cost_priority);
    }
  }, [data]);

  const handleSelect = (materialId: string) => {
    const newSet = new Set(selectedMaterials);
    if (newSet.has(materialId)) newSet.delete(materialId);
    else newSet.add(materialId);
    setSelectedMaterials(newSet);
  };

  const handlePriorityChange = (prio: string) => {
    setActivePriority(prio);
    priorityMut.mutate(prio);
  };

  if (isLoading || generateMut.isPending || priorityMut.isPending) {
    return (
      <Layout title={t('scenario_result.title')}>
        <div className="mb-6"><DisclaimerBanner /></div>
        <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
          <p className="text-gray-600 font-medium">
            {priorityMut.isPending ? 'Re-optimizing multi-attribute ranking & cost models...' : t('scenario_result.running_engine')}
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          <div className="lg:col-span-1"><LoadingSkeleton rows={8} /></div>
          <div className="lg:col-span-2"><LoadingSkeleton rows={12} /></div>
        </div>
      </Layout>
    );
  }

  if (isError || generateMut.isError) {
    return (
      <Layout title={t('scenario_result.title')}>
        <div className="mb-6"><DisclaimerBanner /></div>
        <ErrorBox message={t('scenario_result.error_failed')} />
        <button onClick={() => refetch()} className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg">{t('scenario_result.error_retry')}</button>
      </Layout>
    );
  }

  if (!data) return null;

  const {
    scenario,
    requirement_bands,
    ranking_mode,
    engine_notes,
    final_ranking,
    excluded_with_reasons,
    shelf_life_estimate,
    pareto_picks
  } = data;

  const evaluatedCount = final_ranking.length + excluded_with_reasons.length;
  const currencySym = (scenario.currency === 'USD' ? '$' : (scenario.currency === 'EUR' ? '€' : '₹'));
  const topPick = final_ranking[0];
  const topCost = topPick?.cost_estimate;

  return (
    <Layout title={t('scenario_result.title')}>
      <div className="mb-6"><DisclaimerBanner /></div>

      {/* Engine & Priority Switcher Header */}
      <div className="bg-white border border-gray-200 shadow-sm rounded-xl p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-3 border-b border-gray-100 pb-3">
          <div className="flex items-center gap-3 text-sm">
            <span className={`px-2.5 py-1 rounded-full font-medium text-xs ${ranking_mode === 'ml' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'}`}>
              {t('scenario_result.ranking_mode')}: {ranking_mode.toUpperCase()}
            </span>
            <span className="text-gray-600 text-xs sm:text-sm">
              {t('scenario_result.materials_evaluated', { evaluated: evaluatedCount })}, {t('scenario_result.materials_excluded', { excluded: excluded_with_reasons.length })}, {t('scenario_result.materials_ranked', { ranked: final_ranking.length })}
            </span>
          </div>
          <button onClick={() => generateMut.mutate()} disabled={generateMut.isPending} className="text-xs font-medium text-emerald-700 hover:text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-md transition-colors border border-emerald-200">
            {t('scenario_result.run_engine')}
          </button>
        </div>

        {/* Priority Filter Tabs */}
        <div>
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Optimization Priority Weighting
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {PRIORITIES.map((p) => {
              const Icon = p.icon;
              const active = activePriority === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handlePriorityChange(p.id)}
                  className={`p-2.5 rounded-lg border text-left flex flex-col justify-between transition-all ${
                    active 
                      ? 'bg-emerald-50 border-emerald-500 ring-2 ring-emerald-500/20 text-emerald-950 font-semibold' 
                      : 'bg-white border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-1.5 text-xs">
                    <Icon size={14} className={active ? 'text-emerald-600' : 'text-gray-400'} />
                    <span>{p.label}</span>
                  </div>
                  <div className="text-[10px] text-gray-500 font-normal mt-1">{p.desc}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* BUDGET WARNING BANNER (IF APPLICABLE) */}
      {topCost?.budget_check?.is_over_budget && (
        <div className="mb-6 p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-xl shadow-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-amber-600 shrink-0 mt-0.5" size={20} />
            <div>
              <h4 className="font-bold text-amber-900 text-sm">Packaging Budget Variance Alert</h4>
              <p className="text-xs text-amber-800 mt-1">
                The top-ranked solution exceeds your target budget by {topCost.budget_check.variance_pct}% ({currencySym}{topCost.cost_per_package.toFixed(2)} vs target {currencySym}{scenario.target_cost_per_package || (scenario.target_total_budget / (scenario.package_quantity || 10000))}).
                Check the <b>Lowest Cost Option</b> in the Pareto comparison below for technically suitable, budget-friendly structures.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 4 PARETO / CHOICE HIGHLIGHT CARDS */}
      {pareto_picks && (
        <div className="mb-6">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Sparkles size={14} className="text-emerald-600" /> 4 Distinct Strategic Decision Options
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* 1. Best Technical */}
            <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-bold text-blue-800 uppercase tracking-wider flex items-center gap-1">
                    <Award size={13} /> Best Performance
                  </span>
                  <span className="text-xs font-bold text-blue-700">Fit {Math.round((pareto_picks.best_technical?.fit_score || 0) * 100)}%</span>
                </div>
                <h4 className="font-bold text-gray-900 text-sm line-clamp-1">{pareto_picks.best_technical?.name || 'N/A'}</h4>
                <p className="text-[11px] text-gray-600 mt-1 line-clamp-2">{pareto_picks.best_technical?.explanation}</p>
              </div>
              <div className="mt-3 pt-2 border-t border-blue-200 flex justify-between items-center text-xs">
                <span className="text-gray-500">Unit Cost:</span>
                <span className="font-bold text-gray-900">{currencySym}{pareto_picks.best_technical?.cost_estimate?.cost_per_package?.toFixed(2) || 'N/A'}</span>
              </div>
            </div>

            {/* 2. Lowest Cost */}
            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                    <TrendingDown size={13} /> Lowest Cost
                  </span>
                  <span className="text-xs font-bold text-emerald-700">{currencySym}{pareto_picks.lowest_cost?.cost_estimate?.cost_per_package?.toFixed(2) || 'N/A'}/pkg</span>
                </div>
                <h4 className="font-bold text-gray-900 text-sm line-clamp-1">{pareto_picks.lowest_cost?.name || 'N/A'}</h4>
                <p className="text-[11px] text-gray-600 mt-1 line-clamp-2">{pareto_picks.lowest_cost?.explanation}</p>
              </div>
              <div className="mt-3 pt-2 border-t border-emerald-200 flex justify-between items-center text-xs">
                <span className="text-gray-500">Tech Fit:</span>
                <span className="font-bold text-emerald-900">{Math.round((pareto_picks.lowest_cost?.fit_score || 0) * 100)}% (Compliant)</span>
              </div>
            </div>

            {/* 3. Most Sustainable */}
            <div className="p-4 rounded-xl border border-teal-200 bg-teal-50/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-bold text-teal-800 uppercase tracking-wider flex items-center gap-1">
                    <Leaf size={13} /> Most Sustainable
                  </span>
                  <span className="text-xs font-bold text-teal-700">Eco {Math.round((pareto_picks.most_sustainable?.sustainability_score || 0) * 100)}%</span>
                </div>
                <h4 className="font-bold text-gray-900 text-sm line-clamp-1">{pareto_picks.most_sustainable?.name || 'N/A'}</h4>
                <p className="text-[11px] text-gray-600 mt-1 line-clamp-2">{pareto_picks.most_sustainable?.explanation}</p>
              </div>
              <div className="mt-3 pt-2 border-t border-teal-200 flex justify-between items-center text-xs">
                <span className="text-gray-500">Unit Cost:</span>
                <span className="font-bold text-gray-900">{currencySym}{pareto_picks.most_sustainable?.cost_estimate?.cost_per_package?.toFixed(2) || 'N/A'}</span>
              </div>
            </div>

            {/* 4. Balanced Value */}
            <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-bold text-purple-800 uppercase tracking-wider flex items-center gap-1">
                    <Scale size={13} /> Balanced Value
                  </span>
                  <span className="text-xs font-bold text-purple-700">Match {Math.round((pareto_picks.balanced_value?.combined_score || 0) * 100)}%</span>
                </div>
                <h4 className="font-bold text-gray-900 text-sm line-clamp-1">{pareto_picks.balanced_value?.name || 'N/A'}</h4>
                <p className="text-[11px] text-gray-600 mt-1 line-clamp-2">{pareto_picks.balanced_value?.explanation}</p>
              </div>
              <div className="mt-3 pt-2 border-t border-purple-200 flex justify-between items-center text-xs">
                <span className="text-gray-500">Unit Cost:</span>
                <span className="font-bold text-gray-900">{currencySym}{pareto_picks.balanced_value?.cost_estimate?.cost_per_package?.toFixed(2) || 'N/A'}</span>
              </div>
            </div>

          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-20">
        
        {/* LEFT COLUMN */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Packaging Cost Summary Card */}
          {topCost && (
            <div className="bg-white rounded-xl shadow-sm border border-emerald-200 p-5 border-t-4 border-t-emerald-600">
              <div className="flex justify-between items-center mb-3 border-b pb-2">
                <h3 className="font-bold text-gray-900 text-sm flex items-center gap-1.5">
                  <DollarSign size={16} className="text-emerald-600" /> Commercial Cost Overview
                </h3>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">
                  {topCost.confidence} Confidence
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-baseline">
                  <span className="text-xs text-gray-500">Unit Cost per Pkg:</span>
                  <span className="text-2xl font-black text-emerald-700">{currencySym}{topCost.cost_per_package.toFixed(2)}</span>
                </div>

                {topCost.cost_per_kg_food && (
                  <div className="flex justify-between items-baseline text-xs">
                    <span className="text-gray-500">Cost per kg of Food:</span>
                    <span className="font-semibold text-gray-900">{currencySym}{topCost.cost_per_kg_food.toFixed(2)} / kg</span>
                  </div>
                )}

                <div className="flex justify-between items-baseline text-xs">
                  <span className="text-gray-500">Total Batch ({scenario.package_quantity?.toLocaleString() || '10,000'} pkgs):</span>
                  <span className="font-bold text-gray-900">{currencySym}{topCost.total_batch_cost.toLocaleString()}</span>
                </div>

                {/* Progress bar of material vs converting */}
                <div className="pt-2">
                  <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                    <span>Material Resin ({topCost.material_cost_share_pct}%)</span>
                    <span>Converting & Sealing ({topCost.operations_cost_share_pct}%)</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden flex">
                    <div className="bg-emerald-600 h-full" style={{ width: `${topCost.material_cost_share_pct}%` }}></div>
                    <div className="bg-blue-500 h-full" style={{ width: `${topCost.operations_cost_share_pct}%` }}></div>
                  </div>
                </div>

                <div className="text-[10px] text-gray-400 italic pt-1">
                  *Indicative estimate based on {topCost.price_source}. Polymer resin: {currencySym}{topCost.price_per_kg}/kg @ {topCost.material_density_g_cm3} g/cm³.
                </div>
              </div>
            </div>
          )}

          {/* Scenario Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex justify-between items-start mb-4 border-b pb-2">
              <h3 className="font-semibold text-gray-900 text-sm">{t('scenario_result.scenario_summary')}</h3>
              <button onClick={() => navigate(`/scenarios/new?edit=${scenario.id}`)} className="text-xs text-blue-600 hover:underline">{t('scenario_result.edit_scenario')}</button>
            </div>
            
            <div className="space-y-3 text-sm">
              <div>
                <div className="flex justify-between items-center mb-0.5">
                  <span className="text-gray-500 block text-xs uppercase">{t('scenario_result.commodity')}</span>
                  <EvidenceBadge type="Verified" />
                </div>
                <span className="font-medium text-gray-900 flex items-center gap-2">
                  {scenario.commodity_name}
                  {scenario.commodity_category === 'fresh_produce' && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-800">
                      <Leaf size={10} /> {t('scenario_result.respiring_produce')}
                    </span>
                  )}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500 block uppercase">Format</span>
                  <span className="font-medium text-gray-900 capitalize">{scenario.package_format || 'Pouch'}</span>
                </div>
                <div>
                  <span className="text-gray-500 block uppercase">Fill Weight</span>
                  <span className="font-medium text-gray-900">{scenario.product_weight_g || 100} g</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500 block uppercase">Batch Qty</span>
                  <span className="font-medium text-gray-900">{scenario.package_quantity?.toLocaleString() || '10,000'}</span>
                </div>
                <div>
                  <span className="text-gray-500 block uppercase">Currency</span>
                  <span className="font-medium text-gray-900">{scenario.currency || 'INR'} ({currencySym})</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs border-t pt-2">
                <div>
                  <span className="text-gray-500 block uppercase">{t('scenario_result.storage')}</span>
                  <span className="font-medium text-gray-900 capitalize">{scenario.storage_type}</span>
                </div>
                <div>
                  <span className="text-gray-500 block uppercase">{t('scenario_result.shelf_life_target')}</span>
                  <span className="font-medium text-gray-900">{scenario.target_shelf_life_days} days</span>
                </div>
              </div>
            </div>
          </div>

          {/* Requirement Bands */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4 border-b pb-2 text-sm">{t('scenario_result.requirement_bands')}</h3>
            <div className="space-y-4 text-sm">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Wind size={16} className="text-blue-500" />
                  <span className="font-semibold text-gray-800 text-xs">{t('scenario_result.otr_target')}</span>
                </div>
                <div className="text-base font-bold text-gray-900">{requirement_bands.otr_target}</div>
              </div>
              
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Droplets size={16} className="text-cyan-500" />
                  <span className="font-semibold text-gray-800 text-xs">{t('scenario_result.wvtr_target')}</span>
                </div>
                <div className="text-base font-bold text-gray-900">{requirement_bands.wvtr_target}</div>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Package size={16} className="text-amber-500" />
                  <span className="font-semibold text-gray-800 text-xs">{t('scenario_result.thickness_target')}</span>
                </div>
                <div className="text-base font-bold text-gray-900">{requirement_bands.thickness_target_microns}</div>
              </div>
            </div>
          </div>

          {/* Shelf Life Estimate */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 border-t-4 border-t-emerald-500">
            <h3 className="font-semibold text-gray-900 mb-4 border-b pb-2 text-sm">{t('scenario_result.shelf_life_estimate')}</h3>
            <div className="text-3xl font-bold text-emerald-700 mb-1">
              {shelf_life_estimate.min_days} – {shelf_life_estimate.max_days} <span className="text-sm font-normal text-gray-500">days</span>
            </div>
            <div className="mb-3">
              <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 text-[10px] uppercase font-bold rounded">
                {shelf_life_estimate.confidence}
              </span>
            </div>
            
            <p className="text-xs text-gray-500 uppercase">{t('scenario_result.dominant_failure_mode')}</p>
            <p className="text-xs font-medium text-amber-800 bg-amber-50 rounded px-2 py-1 mt-1 border border-amber-200 inline-block">
              {shelf_life_estimate.dominant_failure_mode}
            </p>
          </div>

        </div>

        {/* RIGHT COLUMN */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* PROMINENT ESTIMATED PACKAGING COST BANNER */}
          {topCost && (
            <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white rounded-xl p-5 shadow-md border border-emerald-700/40">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3 mb-4">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5">
                    <DollarSign size={15} /> Estimated Product Packaging Cost
                  </span>
                  <h3 className="text-lg font-bold text-white mt-0.5">
                    {topPick?.name || 'Top-Ranked Structure'} — {currencySym}{topCost.cost_per_package.toFixed(2)} <span className="text-xs font-normal text-emerald-200">/ package</span>
                  </h3>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-gray-300 uppercase block">Total Batch Estimate</span>
                  <span className="text-xl font-black text-emerald-300">
                    {currencySym}{topCost.total_batch_cost.toLocaleString()}
                  </span>
                  <span className="text-[11px] text-gray-300 block">({scenario.package_quantity?.toLocaleString() || '10,000'} packs)</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2.5 border border-white/10">
                  <span className="text-[10px] uppercase text-emerald-200 block">Unit Pack Cost</span>
                  <span className="text-base font-black text-white">{currencySym}{topCost.cost_per_package.toFixed(2)}</span>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2.5 border border-white/10">
                  <span className="text-[10px] uppercase text-emerald-200 block">Cost / kg Food</span>
                  <span className="text-base font-black text-white">{currencySym}{topCost.cost_per_kg_food?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2.5 border border-white/10">
                  <span className="text-[10px] uppercase text-emerald-200 block">Material Resin</span>
                  <span className="text-base font-black text-emerald-300">{topCost.material_cost_share_pct || 65}%</span>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2.5 border border-white/10">
                  <span className="text-[10px] uppercase text-emerald-200 block">Converting & Seal</span>
                  <span className="text-base font-black text-blue-300">{topCost.operations_cost_share_pct || 35}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Engine Notes (if any) */}
          {engine_notes && engine_notes.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900">
              <h4 className="font-semibold mb-1 flex items-center gap-2"><FlaskConical size={16} /> {t('scenario_result.engine_notes')}</h4>
              <ul className="list-disc pl-5 space-y-1 text-xs">
                {engine_notes.map((n: string, i: number) => <li key={i}>{n}</li>)}
              </ul>
            </div>
          )}

          {/* Ranked Materials */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-gray-900">{t('scenario_result.ranked_materials')}</h3>
                <p className="text-xs text-gray-500 mt-0.5">Ranked by {activePriority.replace('_', ' ')} weighting with technical & packaging cost verification</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full">
                {final_ranking.length} Viable Options
              </span>
            </div>
            
            <div className="p-5">
              {final_ranking.length === 0 ? (
                <div className="text-center py-8">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-500 mb-4">
                    <XCircle size={32} />
                  </div>
                  <h4 className="text-lg font-bold text-gray-900 mb-2">{t('scenario_result.no_material_meets')}</h4>
                  <p className="text-gray-500">Please review the excluded materials below to understand why.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {final_ranking.map((item: any) => (
                    <MaterialCard 
                      key={item.material_id} 
                      item={item} 
                      currencySym={currencySym}
                      selected={selectedMaterials.has(item.material_id)}
                      onToggleSelect={() => handleSelect(item.material_id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Chart Section */}
          {final_ranking.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-4 text-sm">Cost Efficiency vs. Technical Suitability Trade-off</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="cost_score" name="Cost Score" domain={[0, 1]} tickFormatter={(v) => `${Math.round(v*100)}%`} />
                    <YAxis type="number" dataKey="fit_score" name="Technical Fit" domain={[0, 1]} tickFormatter={(v) => `${Math.round(v*100)}%`} />
                    <ZAxis type="number" range={[100, 100]} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value: any) => `${Math.round(Number(value || 0) * 100)}%`} />
                    <Legend />
                    <Scatter name="Candidate Materials" data={final_ranking.slice(0, 8)} fill="#10b981" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Validation Passport Section */}
          <div className="bg-white rounded-xl shadow-sm border border-blue-200 overflow-hidden">
            <div className="px-5 py-4 bg-gradient-to-r from-blue-900 to-indigo-900 text-white flex justify-between items-center">
              <div>
                <h3 className="font-bold flex items-center gap-2 text-base">
                  <ShieldCheck size={18} className="text-blue-300" />
                  Auto-Generated Validation Passport (Laboratory Checklist)
                </h3>
                <p className="text-xs text-blue-200">
                  Ready-made NABL laboratory compliance checklist required prior to commercial scale-up.
                </p>
              </div>
              <EvidenceBadge type="Verified" />
            </div>

            <div className="p-5 overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-gray-100 text-gray-700 uppercase font-semibold">
                  <tr>
                    <th className="p-2.5 rounded-l">Standard Protocol</th>
                    <th className="p-2.5">Designation</th>
                    <th className="p-2.5">Target Barrier Band</th>
                    <th className="p-2.5 rounded-r">Commercial Action Item</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 text-gray-800">
                  <tr>
                    <td className="p-2.5 font-bold">Oxygen Transmission Rate (OTR)</td>
                    <td className="p-2.5 font-mono text-blue-700">ASTM D3985</td>
                    <td className="p-2.5 font-semibold text-emerald-800">{requirement_bands.otr_target}</td>
                    <td className="p-2.5 text-gray-600">Submit film coupon to NABL accredited coulometric chamber</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-bold">Water Vapor Transmission Rate (WVTR)</td>
                    <td className="p-2.5 font-mono text-cyan-700">ASTM F1249</td>
                    <td className="p-2.5 font-semibold text-emerald-800">{requirement_bands.wvtr_target}</td>
                    <td className="p-2.5 text-gray-600">Evaluate under 38°C / 90% RH tropical chamber conditions</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-bold">Seal Integrity & Hermeticity</td>
                    <td className="p-2.5 font-mono text-purple-700">ASTM F88 / ASTM F2029</td>
                    <td className="p-2.5 font-semibold">≥ 15 N / 15mm width</td>
                    <td className="p-2.5 text-gray-600">Seal strength validation and hot tack testing</td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-bold">Accelerated Shelf Life Testing (ASLT)</td>
                    <td className="p-2.5 font-mono text-gray-700">MoFPI / IS 10171</td>
                    <td className="p-2.5 font-semibold">{scenario.target_shelf_life_days} days target</td>
                    <td className="p-2.5 text-gray-600">40°C / 75% RH 30-day accelerated incubator protocol</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Excluded Materials */}
          {excluded_with_reasons.length > 0 && (
            <ExcludedMaterialsSection excluded={excluded_with_reasons} t={t} />
          )}

        </div>
      </div>

      {/* Sticky Action Bar */}
      <div className="fixed bottom-0 left-0 lg:left-64 right-0 bg-white border-t border-gray-200 p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-40 flex justify-between items-center">
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors">
          <ArrowLeft size={16} /> {t('scenario_result.back_dashboard')}
        </button>
        <div className="flex gap-3">
          <button 
            onClick={async () => {
              let recId = data.recommendation_id;
              if (!recId) {
                const genRes = await generateMut.mutateAsync();
                recId = genRes.recommendation_id;
              }
              if (recId) {
                generateReportMut.mutate(recId);
              }
            }}
            disabled={generateReportMut.isPending || selectedMaterials.size === 0}
            className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
          >
            <FileDown size={18} /> {t('scenario_result.generate_report')} ({selectedMaterials.size})
          </button>
        </div>
      </div>

    </Layout>
  );
};

const MaterialCard = ({ item, selected, onToggleSelect, currencySym }: any) => {
  const [expanded, setExpanded] = useState(item.rank === 1);
  const scorePct = Math.round(item.combined_score * 100);
  const cEst = item.cost_estimate || item.cost_breakdown;
  const unitCost = cEst?.total_cost_per_pkg || cEst?.cost_per_package || item.cost_per_pkg || 0;
  const foodCost = cEst?.cost_per_kg_food || item.cost_per_kg_food || 0;
  const batchCost = cEst?.total_batch_cost || item.total_batch_cost || 0;

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${item.rank === 1 ? 'border-emerald-500 shadow-md ring-1 ring-emerald-200' : 'border-gray-200 hover:border-gray-300'}`}>
      
      {/* Header */}
      <div className={`p-4 flex flex-wrap items-center justify-between gap-3 cursor-pointer ${item.rank === 1 ? 'bg-emerald-50/60' : 'bg-white'}`} onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3 sm:gap-4">
          <div onClick={(e) => { e.stopPropagation(); onToggleSelect(); }} className={`w-6 h-6 rounded border flex items-center justify-center cursor-pointer transition-colors ${selected ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-white border-gray-300'}`}>
            {selected && <CheckCircle2 size={16} />}
          </div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${item.rank === 1 ? 'bg-emerald-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600'}`}>
            #{item.rank}
          </div>
          <div>
            <h4 className="font-bold text-gray-900 text-base sm:text-lg">{item.name}</h4>
            
            {/* Packaging Cost Pill */}
            <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600 mt-1">
              <span className="font-bold text-emerald-800 bg-emerald-100/90 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                <DollarSign size={12} /> {currencySym}{unitCost.toFixed(2)} / pack
              </span>
              {foodCost > 0 && (
                <span className="font-medium text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                  {currencySym}{foodCost.toFixed(2)} / kg food
                </span>
              )}
              {batchCost > 0 && (
                <span className="text-gray-500 hidden sm:inline">
                  Batch: {currencySym}{batchCost.toLocaleString()}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4 sm:gap-6">
          <div className="flex flex-col items-end">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-0.5">Overall Fit</div>
            <div className={`text-2xl font-black ${scorePct >= 80 ? 'text-emerald-600' : scorePct >= 60 ? 'text-amber-500' : 'text-red-500'}`}>
              {scorePct}%
            </div>
          </div>
          {expanded ? <ChevronUp className="text-gray-400" /> : <ChevronDown className="text-gray-400" />}
        </div>
      </div>
      
      {/* Body */}
      {expanded && (
        <div className="border-t border-gray-100 bg-white">
          <div className="p-5 space-y-6">
            
            {/* Sub-scores with Multi-Attribute Breakdown */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider flex flex-wrap items-center justify-between gap-1">
                <span>Multi-Attribute Score Composition</span>
                <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Formula: (Tech × {Math.round((item.applied_weights?.technical_weight ?? 0.60) * 100)}%) + (Cost × {Math.round((item.applied_weights?.cost_weight ?? 0.25) * 100)}%) + (Eco × {Math.round((item.applied_weights?.eco_weight ?? 0.15) * 100)}%) = {scorePct}%
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <ScoreBadge 
                  label="Technical Fit" 
                  score={item.technical_score ?? item.raw_fit_score ?? item.fit_score} 
                  weight={item.score_breakdown?.technical_weight ?? item.applied_weights?.technical_weight ?? 0.60}
                  contribution={item.score_breakdown?.technical_contribution ?? ((item.technical_score ?? item.raw_fit_score ?? item.fit_score) * 0.60)}
                />
                <ScoreBadge 
                  label="Cost Score" 
                  score={item.cost_score ?? 0.50} 
                  weight={item.score_breakdown?.cost_weight ?? item.applied_weights?.cost_weight ?? 0.25}
                  contribution={item.score_breakdown?.cost_contribution ?? ((item.cost_score ?? 0.50) * 0.25)}
                />
                <ScoreBadge 
                  label="Sustainability (Eco)" 
                  score={item.eco_score ?? item.sustainability_score ?? 0.50} 
                  weight={item.score_breakdown?.eco_weight ?? item.applied_weights?.eco_weight ?? 0.15}
                  contribution={item.score_breakdown?.eco_contribution ?? ((item.eco_score ?? 0.50) * 0.15)}
                />
              </div>
            </div>

            {/* DETAILED COST BREAKDOWN TABLE */}
            {cEst && (
              <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <h5 className="text-xs font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                    <DollarSign size={15} className="text-emerald-700" /> Estimated Packaging Cost & Itemized BOM
                  </h5>
                  <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-200">
                    {cEst.confidence || 'Commercial'} Confidence ({cEst.price_source || 'Market Benchmarks'})
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-3">
                  <div className="p-2.5 bg-white rounded-lg border border-emerald-100 shadow-xs">
                    <span className="text-gray-400 text-[10px] uppercase block font-medium">Estimated Pack Cost</span>
                    <span className="text-sm font-black text-emerald-800">{currencySym}{unitCost.toFixed(2)}</span>
                    <span className="text-[10px] text-gray-500 block">per individual pack</span>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-emerald-100 shadow-xs">
                    <span className="text-gray-400 text-[10px] uppercase block font-medium">Cost / kg Food</span>
                    <span className="text-sm font-black text-gray-800">{currencySym}{foodCost.toFixed(2)}</span>
                    <span className="text-[10px] text-gray-500 block">packaging to food ratio</span>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-emerald-100 shadow-xs">
                    <span className="text-gray-400 text-[10px] uppercase block font-medium">Raw Polymer Mass</span>
                    <span className="text-sm font-bold text-gray-800">{(cEst.material_mass_g || cEst.material_mass_grams || 0).toFixed(2)} g</span>
                    <span className="text-[10px] text-gray-500 block">{currencySym}{(cEst.raw_material_cost || cEst.material_cost_per_pkg || 0).toFixed(3)} resin</span>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-emerald-100 shadow-xs">
                    <span className="text-gray-400 text-[10px] uppercase block font-medium">Converting & Sealing</span>
                    <span className="text-sm font-bold text-gray-800">
                      {currencySym}{((cEst.converting_cost || cEst.conversion_cost_per_pkg || 0) + (cEst.sealing_cost || cEst.sealing_cost_per_pkg || 0)).toFixed(3)}
                    </span>
                    <span className="text-[10px] text-gray-500 block">+ {currencySym}{(cEst.scrap_wastage_cost || cEst.wastage_cost_per_pkg || 0).toFixed(3)} scrap</span>
                  </div>
                </div>

                {cEst.assumptions && cEst.assumptions.length > 0 && (
                  <div className="text-[11px] text-emerald-900 bg-white/90 p-2.5 rounded-lg border border-emerald-200/80">
                    <span className="font-bold">Procurement Assumptions: </span>
                    {cEst.assumptions.join(' • ')}
                  </div>
                )}
              </div>
            )}

            {/* Specs Grid */}
            <div>
              <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Key Technical Specifications</h5>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 bg-gray-50 rounded-lg border border-gray-100">
                <SpecItem label="OTR" value={item.otr} unit="cc/m²/d" />
                <SpecItem label="WVTR" value={item.wvtr} unit="g/m²/d" />
                <SpecItem label="Thickness" value={item.thickness_microns} unit="µm" />
                <SpecItem label="Food Safe" value={item.food_contact_safe ? 'Yes' : 'No'} isBool boolVal={item.food_contact_safe} />
                <SpecItem label="Recyclable" value={item.recyclable ? 'Yes' : 'No'} isBool boolVal={item.recyclable} />
              </div>
            </div>
            
            {/* Explanation & Trade-offs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Why this material?</h5>
                <p className="text-sm text-gray-700 leading-relaxed">{item.explanation}</p>
              </div>
              
              {item.trade_offs && (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Trade-offs</h5>
                  <div className="space-y-3">
                    {item.trade_offs.pros && item.trade_offs.pros.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-emerald-700 mb-1 flex items-center gap-1"><CheckCircle2 size={12}/> Pros</div>
                        <ul className="text-xs text-gray-600 list-disc pl-4 space-y-0.5">
                          {item.trade_offs.pros.map((p: string, i: number) => <li key={i}>{p}</li>)}
                        </ul>
                      </div>
                    )}
                    {item.trade_offs.cons && item.trade_offs.cons.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-amber-700 mb-1 flex items-center gap-1"><XCircle size={12}/> Cons</div>
                        <ul className="text-xs text-gray-600 list-disc pl-4 space-y-0.5">
                          {item.trade_offs.cons.map((c: string, i: number) => <li key={i}>{c}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

const ScoreBadge = ({ label, score, weight, contribution }: { label: string, score: number, weight?: number, contribution?: number }) => {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 75 ? 'bg-emerald-100 text-emerald-900 border-emerald-300' : pct >= 50 ? 'bg-amber-100 text-amber-900 border-amber-300' : 'bg-red-100 text-red-900 border-red-300';
  return (
    <div className={`p-2.5 rounded-lg flex flex-col justify-between border ${color}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-bold uppercase">{label}</span>
        <span className="text-base font-black">{pct}%</span>
      </div>
      {weight !== undefined && (
        <div className="text-[10px] opacity-85 mt-1 border-t border-black/10 pt-1 flex justify-between">
          <span>Weight: {Math.round(weight * 100)}%</span>
          {contribution !== undefined && <span className="font-semibold">Contrib: +{Math.round(contribution * 100)}%</span>}
        </div>
      )}
    </div>
  );
};

const SpecItem = ({ label, value, unit, isBool, boolVal }: any) => (
  <div>
    <div className="text-[10px] text-gray-500 uppercase font-semibold mb-1">{label}</div>
    <div className="font-medium text-gray-900 flex items-center gap-1.5 text-sm">
      {isBool && (boolVal ? <CheckCircle2 size={14} className="text-emerald-500" /> : <XCircle size={14} className="text-red-500" />)}
      {value} {unit && <span className="text-gray-400 text-xs">{unit}</span>}
    </div>
  </div>
);

const ExcludedMaterialsSection = ({ excluded, t }: any) => {
  const [open, setOpen] = useState(false);
  
  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <button 
        className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-gray-100 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="font-medium text-gray-700">
          {open ? t('scenario_result.hide_excluded_materials') : t('scenario_result.excluded_materials_title', { count: excluded.length })}
        </span>
        {open ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
      </button>
      
      {open && (
        <div className="p-5 border-t border-gray-200">
          <div className="space-y-3">
            {excluded.map((ex: any, i: number) => (
              <div key={i} className="bg-white border border-gray-200 p-3 rounded-lg flex flex-col sm:flex-row sm:items-start gap-2">
                <div className="font-semibold text-gray-900 min-w-[200px]">{ex.name}</div>
                <div className="text-sm text-red-600 bg-red-50 px-2 py-1 rounded inline-block">{ex.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScenarioResult;


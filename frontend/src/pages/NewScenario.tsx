import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import Layout from '../components/layout/Layout';
import { createScenario } from '../services/scenarioApi';
import { ErrorBox } from '../components/ui/Shared';
import { ArrowRight, Check, Sparkles, DollarSign, Sliders, Info } from 'lucide-react';

interface ScenarioFormData {
  commodity_name: string;
  commodity_category: string;
  moisture_pct?: number | string | null;
  fat_pct?: number | string | null;
  ph?: number | string | null;
  respiration_rate?: number | string | null;
  storage_type: string;
  target_rh?: number | string | null;
  temp_min?: number | string | null;
  temp_max?: number | string | null;
  transport_mode?: string;
  transport_days?: number | string | null;
  target_shelf_life_days: number | string;
  // Cost & Production Fields
  cost_priority: string;
  package_format: string;
  product_weight_g?: number | string | null;
  package_quantity?: number | string | null;
  currency: string;
  target_cost_per_package?: number | string | null;
  target_total_budget?: number | string | null;
  // Advanced fields
  package_length_cm?: number | string | null;
  package_width_cm?: number | string | null;
  package_height_cm?: number | string | null;
  film_area_cm2?: number | string | null;
  custom_thickness_um?: number | string | null;
  layer_count?: number | string | null;
  closure_cost_per_pkg?: number | string | null;
  label_cost_per_pkg?: number | string | null;
  printing_cost_per_pkg?: number | string | null;
  secondary_pack_cost_per_pkg?: number | string | null;
  labor_packing_cost_per_pkg?: number | string | null;
  transport_cost_per_pkg?: number | string | null;
  wastage_pct_override?: number | string | null;
}

const CATEGORIES = [
  { value: 'fresh_produce', label: 'Fresh Produce (Vegetables / Fruits)' },
  { value: 'dry', label: 'Dry Foods / Pulses / Grains / Spices' },
  { value: 'oily', label: 'Oily Foods / Crisps / Fried Snacks' },
  { value: 'dairy', label: 'Dairy / Butter / Paneer' },
  { value: 'processed', label: 'Processed / Ready-to-Eat / Retort' },
];

const STORAGE = [
  { value: 'ambient', label: 'Ambient Room Temp (15°C to 35°C)' },
  { value: 'chilled', label: 'Chilled Cold Storage (0°C to 8°C)' },
  { value: 'frozen', label: 'Frozen Deep Cold (<-18°C)' },
];

const FORMATS = [
  { value: 'pouch', label: 'Pouch / Pillow Pouch (Standup / 3-Side Seal)' },
  { value: 'bag', label: 'Bag / Gusseted Bulk Bag' },
  { value: 'sachet', label: 'Sachet / Single-Serve Stick Pack' },
  { value: 'tray_lidding', label: 'Tray with Barrier Lidding Film' },
  { value: 'bottle', label: 'Rigid Bottle / Canister' },
  { value: 'jar', label: 'Rigid Jar / Tub' },
  { value: 'carton_box', label: 'Folding Carton / Cardboard Box' },
  { value: 'crate_bulk', label: 'Crate / Corrugated Bulk Master Pack' },
  { value: 'custom', label: 'Custom / Tailored Format' },
];

const PRIORITIES = [
  { value: 'balanced', label: 'Balanced (60% Performance, 25% Cost, 15% Eco)', desc: 'Optimal trade-off for commercial viability & safety' },
  { value: 'cost_first', label: 'Lowest Cost First (50% Cost, 40% Performance, 10% Eco)', desc: 'Prioritizes minimum packaging bill of materials' },
  { value: 'performance_first', label: 'Best Technical Performance (80% Performance, 10% Cost, 10% Eco)', desc: 'Prioritizes maximum barrier & shelf life margin' },
  { value: 'sustainability_first', label: 'Most Sustainable (40% Eco, 45% Performance, 15% Cost)', desc: 'Prioritizes biodegradable / recyclable circular polymers' },
];

const PRESETS = [
  {
    name: 'Potato Chips / Crisps (100g)',
    commodity_name: 'Potato Chips',
    commodity_category: 'oily',
    moisture_pct: 2.0,
    fat_pct: 35.0,
    ph: 6.0,
    storage_type: 'ambient',
    target_rh: 50.0,
    target_shelf_life_days: 120,
    transport_mode: 'road',
    transport_days: 3,
    package_format: 'pouch',
    product_weight_g: 100,
    package_quantity: 25000,
    currency: 'INR',
    cost_priority: 'cost_first',
    package_length_cm: 20,
    package_width_cm: 15,
  },
  {
    name: 'Fresh Tomatoes (500g Tray)',
    commodity_name: 'Fresh Tomatoes',
    commodity_category: 'fresh_produce',
    moisture_pct: 94.0,
    fat_pct: 0.2,
    ph: 4.3,
    respiration_rate: 28.0,
    storage_type: 'chilled',
    target_rh: 90.0,
    target_shelf_life_days: 18,
    transport_mode: 'cold_chain',
    transport_days: 2,
    package_format: 'tray_lidding',
    product_weight_g: 500,
    package_quantity: 10000,
    currency: 'INR',
    cost_priority: 'balanced',
    package_length_cm: 18,
    package_width_cm: 14,
    package_height_cm: 6,
  },
  {
    name: 'Basmati Rice (1 kg Bag)',
    commodity_name: 'Basmati Rice',
    commodity_category: 'dry',
    moisture_pct: 12.0,
    fat_pct: 0.5,
    ph: 6.8,
    storage_type: 'ambient',
    target_rh: 60.0,
    target_shelf_life_days: 365,
    transport_mode: 'road',
    transport_days: 5,
    package_format: 'bag',
    product_weight_g: 1000,
    package_quantity: 50000,
    currency: 'INR',
    cost_priority: 'cost_first',
  },
  {
    name: 'Organic Green Peas (250g)',
    commodity_name: 'Frozen Green Peas',
    commodity_category: 'processed',
    moisture_pct: 78.0,
    fat_pct: 0.4,
    ph: 6.5,
    storage_type: 'frozen',
    target_rh: 85.0,
    target_shelf_life_days: 180,
    transport_mode: 'cold_chain',
    transport_days: 4,
    package_format: 'pouch',
    product_weight_g: 250,
    package_quantity: 15000,
    currency: 'INR',
    cost_priority: 'sustainability_first',
  }
];

const NewScenario: React.FC = () => {
  const [step, setStep] = useState(1);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showAdvancedCost, setShowAdvancedCost] = useState(false);
  const [presetNotice, setPresetNotice] = useState('');
  const navigate = useNavigate();
  const { register, handleSubmit, watch, setValue } = useForm<ScenarioFormData>({
    defaultValues: {
      commodity_name: '',
      commodity_category: '',
      storage_type: 'ambient',
      target_shelf_life_days: 30,
      transport_mode: 'road',
      transport_days: 3,
      cost_priority: 'balanced',
      package_format: 'pouch',
      product_weight_g: 100,
      package_quantity: 10000,
      currency: 'INR',
    }
  });

  const category = watch('commodity_category');

  const applyPreset = (preset: typeof PRESETS[0]) => {
    Object.entries(preset).forEach(([k, v]) => {
      setValue(k as any, v);
    });
    setPresetNotice(`Loaded preset for "${preset.name}". You can adjust any values before proceeding.`);
  };

  const onSubmit = async (data: any) => {
    if (step < 4) {
      setStep(step + 1);
      return;
    }
    
    setError('');
    setSubmitting(true);
    try {
      const payload = { ...data };
      const numericFields = [
        'moisture_pct', 'fat_pct', 'ph', 'respiration_rate', 'target_rh', 'temp_min', 'temp_max', 'transport_days',
        'product_weight_g', 'package_quantity', 'target_cost_per_package', 'target_total_budget',
        'package_length_cm', 'package_width_cm', 'package_height_cm', 'film_area_cm2', 'custom_thickness_um',
        'layer_count', 'closure_cost_per_pkg', 'label_cost_per_pkg', 'printing_cost_per_pkg',
        'secondary_pack_cost_per_pkg', 'labor_packing_cost_per_pkg', 'transport_cost_per_pkg', 'wastage_pct_override'
      ];
      
      numericFields.forEach(k => {
        if (payload[k] === '' || payload[k] === undefined || isNaN(parseFloat(payload[k]))) {
          payload[k] = null;
        } else {
          payload[k] = parseFloat(payload[k]);
        }
      });

      payload.target_shelf_life_days = parseInt(payload.target_shelf_life_days, 10);
      if (payload.package_quantity) payload.package_quantity = parseInt(payload.package_quantity, 10);
      if (payload.layer_count) payload.layer_count = parseInt(payload.layer_count, 10);
      
      const res = await createScenario(payload);
      navigate(`/scenario/${res.id}/results?generate=true`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create scenario.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout title="New Packaging Recommendation Scenario">
      <div className="max-w-3xl mx-auto">
        {/* Progress Bar (4 Steps) */}
        <div className="mb-8 flex items-center justify-between relative">
          <div className="absolute left-0 top-1/2 w-full h-0.5 bg-gray-200 -z-10 -translate-y-1/2"></div>
          <div className="absolute left-0 top-1/2 h-0.5 bg-emerald-600 -z-10 -translate-y-1/2 transition-all" style={{ width: `${((step - 1) / 3) * 100}%` }}></div>
          {[
            { n: 1, label: 'Commodity' },
            { n: 2, label: 'Storage' },
            { n: 3, label: 'Cost & Pack' },
            { n: 4, label: 'Shelf Life' }
          ].map(s => (
            <div key={s.n} className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 bg-white transition-colors ${step >= s.n ? 'border-emerald-600 text-emerald-600 font-bold' : 'border-gray-300 text-gray-400'}`}>
                {step > s.n ? <Check size={16} /> : s.n}
              </div>
              <span className="text-[11px] text-gray-500 mt-1 hidden sm:block">{s.label}</span>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
          {error && <div className="mb-6"><ErrorBox message={error} /></div>}

          {/* Quick presets bar on step 1 */}
          {step === 1 && (
            <div className="mb-6 bg-emerald-50/70 border border-emerald-200 rounded-lg p-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 mb-2">
                <Sparkles size={14} /> Quick Demo Commodity Presets
              </div>
              <div className="flex flex-wrap gap-2">
                {PRESETS.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    onClick={() => applyPreset(p)}
                    className="px-2.5 py-1 text-xs bg-white text-emerald-700 border border-emerald-300 rounded hover:bg-emerald-100 transition-colors"
                  >
                    {p.name}
                  </button>
                ))}
              </div>
              {presetNotice && <p className="text-[11px] text-emerald-700 mt-2 italic">{presetNotice}</p>}
            </div>
          )}
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            
            {/* STEP 1: COMMODITY */}
            {step === 1 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                <h3 className="text-xl font-bold text-gray-900 border-b pb-2">1. Commodity Profile</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="col-span-full">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Commodity Name *</label>
                    <input {...register("commodity_name", { required: true })} placeholder="e.g., Potato Chips or Fresh Tomatoes" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                    <select {...register("commodity_category", { required: true })} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none">
                      <option value="">Select Category</option>
                      {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Moisture Content (%)</label>
                    <input type="number" step="0.1" min="0" max="100" {...register("moisture_pct")} placeholder="e.g., 2% for dry/chips, 90% for vegetables" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fat/Oil Content (%)</label>
                    <input type="number" step="0.1" min="0" max="100" {...register("fat_pct")} placeholder="High fat (>15%) triggers oxygen/light barrier" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">pH Level (Acidity)</label>
                    <input type="number" step="0.1" min="1" max="14" {...register("ph")} placeholder="e.g., 4.5 for tomato, 6.8 for grains" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                  </div>
                  {category === 'fresh_produce' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Respiration Rate (mg CO₂/kg/hr)</label>
                      <input type="number" step="0.1" min="0" {...register("respiration_rate")} placeholder="e.g. 20-40 mg CO2/kg/hr for tomato" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                      <p className="text-[11px] text-gray-500 mt-1">High respiration (&gt;50) requires breathable or micro-perforated film (MAP).</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* STEP 2: STORAGE & TRANSPORT */}
            {step === 2 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                <h3 className="text-xl font-bold text-gray-900 border-b pb-2">2. Storage & Transport Envelope</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="col-span-full">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Primary Storage Condition *</label>
                    <select {...register("storage_type", { required: true })} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none">
                      {STORAGE.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Target Relative Humidity (RH %)</label>
                    <input type="number" step="0.1" min="10" max="100" {...register("target_rh")} placeholder="e.g. 50% for dry, 85-90% for cold room" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Transport Mode</label>
                    <select {...register("transport_mode")} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none">
                      <option value="road">Road Freight (Standard)</option>
                      <option value="cold_chain">Cold Chain (Refrigerated Truck)</option>
                      <option value="rail">Rail Transport</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Transit Duration (Days)</label>
                    <input type="number" step="0.5" min="0" {...register("transport_days")} placeholder="e.g. 2 to 5 days" className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: COST & PRODUCTION DETAILS */}
            {step === 3 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    <DollarSign className="text-emerald-600" size={22} /> 3. Cost & Production Details
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowAdvancedCost(!showAdvancedCost)}
                    className="flex items-center gap-1.5 text-xs text-emerald-700 hover:text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-md border border-emerald-200 transition-colors font-medium"
                  >
                    <Sliders size={14} /> {showAdvancedCost ? 'Simple Mode' : 'Advanced Mode'}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Target Package Format *</label>
                    <select {...register("package_format")} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none">
                      {FORMATS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Product Weight per Package (g) *</label>
                    <input
                      type="number"
                      step="1"
                      min="1"
                      {...register("product_weight_g")}
                      placeholder="e.g. 100 for chips, 500 for tray"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Production Batch Quantity (Units) *</label>
                    <input
                      type="number"
                      step="100"
                      min="100"
                      {...register("package_quantity")}
                      placeholder="e.g. 10,000 packages"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Currency *</label>
                    <select {...register("currency")} className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none">
                      <option value="INR">INR (₹) - Indian Rupee</option>
                      <option value="USD">USD ($) - US Dollar</option>
                      <option value="EUR">EUR (€) - Euro</option>
                    </select>
                  </div>

                  <div className="col-span-full">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Recommendation Cost & Performance Priority *</label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {PRIORITIES.map(p => (
                        <label key={p.value} className="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                          <input type="radio" value={p.value} {...register("cost_priority")} className="mt-1 text-emerald-600 focus:ring-emerald-500" />
                          <div>
                            <div className="font-semibold text-xs text-gray-900">{p.label}</div>
                            <div className="text-[11px] text-gray-500 mt-0.5">{p.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Target Max Cost per Package (Optional)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      {...register("target_cost_per_package")}
                      placeholder="e.g. ₹2.50 or $0.05"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Target Total Packaging Budget (Optional)</label>
                    <input
                      type="number"
                      step="100"
                      min="0"
                      {...register("target_total_budget")}
                      placeholder="e.g. ₹50,000 for entire batch"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                    />
                  </div>
                </div>

                {/* ADVANCED COST ACCORDION */}
                {showAdvancedCost && (
                  <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg space-y-4 animate-in fade-in">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-700">
                      <Info size={14} className="text-emerald-600" /> Advanced Dimensions & Custom Converting Line Rates (Overrides defaults)
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Length (cm)</label>
                        <input type="number" step="0.1" {...register("package_length_cm")} placeholder="e.g. 20" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Width (cm)</label>
                        <input type="number" step="0.1" {...register("package_width_cm")} placeholder="e.g. 15" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Height/Gusset (cm)</label>
                        <input type="number" step="0.1" {...register("package_height_cm")} placeholder="e.g. 5" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Direct Film Area (cm²)</label>
                        <input type="number" step="1" {...register("film_area_cm2")} placeholder="Auto-calculated if blank" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Custom Thickness (µm)</label>
                        <input type="number" step="1" {...register("custom_thickness_um")} placeholder="Default: 40 µm" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Wastage Rate Override (%)</label>
                        <input type="number" step="0.5" {...register("wastage_pct_override")} placeholder="Default: 5% - 8%" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Printing Cost / pkg</label>
                        <input type="number" step="0.01" {...register("printing_cost_per_pkg")} placeholder="0.00" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Closure / Cap Cost / pkg</label>
                        <input type="number" step="0.01" {...register("closure_cost_per_pkg")} placeholder="0.00" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Secondary Pack / Crate</label>
                        <input type="number" step="0.01" {...register("secondary_pack_cost_per_pkg")} placeholder="0.00" className="w-full px-3 py-1.5 text-xs border rounded bg-white" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* STEP 4: TARGET & REVIEW */}
            {step === 4 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                <h3 className="text-xl font-bold text-gray-900 border-b pb-2">4. Target Shelf Life & Evaluation</h3>
                <div className="grid grid-cols-1 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Desired Shelf Life (Days) *</label>
                    <input type="number" min="1" max="1095" {...register("target_shelf_life_days", { required: true, min: 1 })} placeholder="e.g. 15 for produce, 120 for chips" className="w-full md:w-1/2 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" />
                    <p className="text-sm text-gray-500 mt-2">
                      The hybrid recommendation engine combines deterministic barrier rules with a machine learning fit scoring pipeline and commercial cost optimization to screen materials and rank the best technical, economic, and sustainable alternatives.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between pt-6 border-t mt-8">
              {step > 1 ? (
                <button type="button" onClick={() => setStep(step - 1)} className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium">Back</button>
              ) : <div></div>}
              
              <button type="submit" disabled={submitting} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50">
                {step === 4 ? (submitting ? 'Analyzing & Ranking Materials...' : 'Analyze & Generate Recommendations') : 'Next Step'} 
                {step < 4 && <ArrowRight size={16} />}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};

export default NewScenario;


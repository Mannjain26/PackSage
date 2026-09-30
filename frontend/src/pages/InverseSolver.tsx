import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import {
  solveInverseRequirements,
  getClimateOptions,
  simulateDowngrade,
  type InverseSolvePayload
} from '../services/solverApi';
import { EvidenceBadge, ErrorBox, LoadingSkeleton } from '../components/ui/Shared';
import {
  TrendingDown,
  Info,
  Volume2,
  Languages,
  SlidersHorizontal,
  Check,
  AlertTriangle,
  FileSpreadsheet,
  MapPin,
  Clock
} from 'lucide-react';

const BHARAT_LANGUAGES = [
  { code: 'hi', name: 'हिन्दी (Hindi)' },
  { code: 'en', name: 'English' },
  { code: 'mr', name: 'मराठी (Marathi)' },
  { code: 'gu', name: 'ગુજરાતી (Gujarati)' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'te', name: 'తెలుగు (Telugu)' }
];

const TRANSLATIONS: Record<string, Record<string, string>> = {
  hi: {
    targetShelfLife: 'लक्षित शेल्फ लाइफ (दिन)',
    moistureProtection: 'नमी से बचाव (WVTR)',
    oxygenProtection: 'ऑक्सीजन व हवा से बचाव (OTR)',
    thickness: 'फिल्म की मोटाई',
    foodSafe: 'खाद्य मानक (FSSAI)',
    summaryText: 'यह पैकेजिंग संरचना नमी और ऑक्सीजन को रोककर आपके उत्पाद को पूरे शेल्फ-लाइफ तक ताज़ा और कुरकुरा बनाए रखेगी।'
  },
  en: {
    targetShelfLife: 'Target Shelf Life (Days)',
    moistureProtection: 'Moisture Ingress Limit (WVTR)',
    oxygenProtection: 'Oxygen Permeability Limit (OTR)',
    thickness: 'Recommended Gauge',
    foodSafe: 'Food Contact Safe (FSSAI)',
    summaryText: 'This packaging barrier prevents moisture ingress, blocks atmospheric oxygen, and keeps food crisp and safe across the supply chain.'
  },
  mr: {
    targetShelfLife: 'अपेक्षित शेल्फ लाइफ (दिवस)',
    moistureProtection: 'ओलावा प्रतिबंध (WVTR)',
    oxygenProtection: 'हवा व ऑक्सिजन प्रतिबंध (OTR)',
    thickness: 'फिल्म जाडी',
    foodSafe: 'अन्न सुरक्षा प्रमाणित',
    summaryText: 'हे पॅकेजिंग ओलावा रोखते, ऑक्सिजन थांबवते आणि अन्न टिकवून ठेवते.'
  },
  gu: {
    targetShelfLife: 'શેલ્ફ લાઇફ (દિવસો)',
    moistureProtection: 'ભેજ સુરક્ષા (WVTR)',
    oxygenProtection: 'ઓક્સિજન સુરક્ષા (OTR)',
    thickness: 'ફિલ્મ જાડાઈ',
    foodSafe: 'ફૂડ ગ્રેડ સુરક્ષિત',
    summaryText: 'આ પેકેજિંગ ભેજ અને હવાને અંદર આવવા દેશે નહીં અને ખોરાકને તાજો રાખશે.'
  },
  pa: {
    targetShelfLife: 'ਸ਼ੈਲਫ ਲਾਈਫ (ਦਿਨ)',
    moistureProtection: 'ਨਮੀ ਤੋਂ ਬਚਾਅ (WVTR)',
    oxygenProtection: 'ਆਕਸੀਜਨ ਰੁਕਾਵਟ (OTR)',
    thickness: 'ਮੋਟਾਈ',
    foodSafe: 'ਫੂਡ ਗ੍ਰੇਡ ਸੇਫ',
    summaryText: 'ਇਹ ਪੈਕੇਜਿੰਗ ਨਮੀ ਅਤੇ ਹਵਾ ਨੂੰ ਰੋਕ ਕੇ ਤੁਹਾਡੇ ਉਤਪਾਦ ਨੂੰ ਤਾਜ਼ਾ ਰੱਖੇਗੀ।'
  },
  te: {
    targetShelfLife: 'షెల్ఫ్ లైఫ్ (రోజులు)',
    moistureProtection: 'తేమ రక్షణ (WVTR)',
    oxygenProtection: 'ఆక్సిజన్ రక్షణ (OTR)',
    thickness: 'మందం',
    foodSafe: 'ఆహార భద్రత ప్రమాణం',
    summaryText: 'ఈ ప్యాకేజింగ్ తేమను, గాలిని అడ్డుకుని ఆహారాన్ని తాజాగా ఉంచుతుంది.'
  }
};

const COMMODITY_PRESETS = [
  {
    id: 'oily',
    label: 'Potato Chips / Fried Snacks',
    badge: 'High Fat + Crisp',
    days: 120,
    weight: 80,
    moisture: 4.5,
    fat: 35.0,
    notes: 'Prone to crispness loss from moisture and rancidity from oxygen.'
  },
  {
    id: 'fresh_produce',
    label: 'Fresh Produce (e.g. Tomatoes)',
    badge: 'Living / Respiration',
    days: 18,
    weight: 500,
    moisture: 92.0,
    fat: 0.2,
    notes: 'Requires controlled gas exchange (MAP) to prevent anaerobic spoilage.'
  },
  {
    id: 'dry',
    label: 'Biscuits / Roasted Grains / Spices',
    badge: 'Moisture Sensitive',
    days: 180,
    weight: 250,
    moisture: 9.0,
    fat: 8.0,
    notes: 'Requires moisture barrier to avoid sogginess, mold, and caking.'
  },
  {
    id: 'dairy',
    label: 'Dairy / Paneer / Butter',
    badge: 'Chilled Perishable',
    days: 30,
    weight: 200,
    moisture: 60.0,
    fat: 25.0,
    notes: 'Microbial activity and oxidative souring under ambient temperature shocks.'
  }
];

export const InverseSolverPage: React.FC = () => {
  // Inputs
  const [commodityCategory, setCommodityCategory] = useState('oily');
  const [shelfLifeDays, setShelfLifeDays] = useState(120);
  const [packWeightGrams, setPackWeightGrams] = useState(80);
  const [cityName, setCityName] = useState('Indore (Malwa / Central Plateau)');
  const [season, setSeason] = useState('standard');
  const [transitMode, setTransitMode] = useState('truck_standard');
  const [coldChainBreakHours, setColdChainBreakHours] = useState(0);

  // Editable Defaults
  const [criticalMoisture, setCriticalMoisture] = useState(4.5);
  const [fatPct, setFatPct] = useState(35.0);
  const [showAdvancedAssumptions, setShowAdvancedAssumptions] = useState(false);

  // Downgrade slider
  const [currentCostIndex, setCurrentCostIndex] = useState(3.5);
  const [targetCostIndex, setTargetCostIndex] = useState(2.0);
  const [downgradeResult, setDowngradeResult] = useState<any>(null);

  // Multilingual & Voice
  const [selectedLang, setSelectedLang] = useState('hi');
  const [speaking, setSpeaking] = useState(false);

  // Data & API state
  const [climateOptions, setClimateOptions] = useState<any>(null);
  const [solverResult, setSolverResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Active Preset Selection
  const applyPreset = (preset: typeof COMMODITY_PRESETS[0]) => {
    setCommodityCategory(preset.id);
    setShelfLifeDays(preset.days);
    setPackWeightGrams(preset.weight);
    setCriticalMoisture(preset.moisture);
    setFatPct(preset.fat);
  };

  useEffect(() => {
    getClimateOptions()
      .then(setClimateOptions)
      .catch((err) => console.error('Could not load climate data', err));
  }, []);

  useEffect(() => {
    runSolver();
  }, [
    commodityCategory,
    shelfLifeDays,
    packWeightGrams,
    cityName,
    season,
    transitMode,
    coldChainBreakHours,
    criticalMoisture,
    fatPct
  ]);

  useEffect(() => {
    simulateDowngrade({
      original_shelf_life_days: shelfLifeDays,
      current_cost_index: currentCostIndex,
      target_cost_index: targetCostIndex,
      commodity_category: commodityCategory
    })
      .then(setDowngradeResult)
      .catch(() => {});
  }, [shelfLifeDays, currentCostIndex, targetCostIndex, commodityCategory]);

  const runSolver = async () => {
    setLoading(true);
    setError('');
    try {
      const payload: InverseSolvePayload = {
        commodity_category: commodityCategory,
        target_shelf_life_days: Number(shelfLifeDays),
        pack_weight_grams: Number(packWeightGrams),
        pack_area_m2: 0.04,
        critical_moisture_pct: Number(criticalMoisture),
        fat_pct: commodityCategory === 'oily' ? Number(fatPct) : undefined,
        city_name: cityName,
        season: season,
        transit_mode: transitMode,
        cold_chain_break_hours: Number(coldChainBreakHours),
        break_temp_c: 35.0
      };
      const res = await solveInverseRequirements(payload);
      setSolverResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to compute requirements. Please verify inputs.');
    } finally {
      setLoading(false);
    }
  };

  const speakPlainLanguage = () => {
    if (!('speechSynthesis' in window)) {
      alert('Your browser does not support audio speech output.');
      return;
    }
    const t = TRANSLATIONS[selectedLang] || TRANSLATIONS['hi'];
    const textToSpeak = `${t.summaryText} ${t.targetShelfLife}: ${shelfLifeDays} दिन।`;
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = selectedLang === 'hi' ? 'hi-IN' : 'en-IN';
    utterance.onend = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const t = TRANSLATIONS[selectedLang] || TRANSLATIONS['en'];
  const activePreset = COMMODITY_PRESETS.find((p) => p.id === commodityCategory);

  return (
    <Layout title="Target Shelf-Life Barrier Calculator">
      
      {/* 1. CLEAN PROFESSIONAL HEADER */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                MoFPI Methodology
              </span>
              <span className="text-xs text-gray-400">IS 10171 / ASTM D3985 / ASTM F1249</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
              Packaging Barrier Target Solver
            </h1>
            <p className="text-sm text-gray-600 mt-1 max-w-3xl leading-relaxed">
              Start with your product's shelf-life goal and transit route. The system works backward to determine the exact maximum barrier limits (WVTR and OTR) your packaging film must provide.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center bg-gray-50 border border-gray-200 p-2 rounded-lg text-xs">
            <Languages size={15} className="text-gray-500" />
            <select
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="bg-transparent font-medium text-gray-700 outline-none cursor-pointer"
            >
              {BHARAT_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && <div className="mb-6"><ErrorBox message={error} /></div>}

      {/* 2. MAIN 2-COLUMN WORKSPACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
        
        {/* LEFT COLUMN: PRODUCT & TRANSIT CONTROLS */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Card: Commodity & Shelf Life */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                <SlidersHorizontal size={16} className="text-emerald-600" />
                Product & Shelf-Life Target
              </h2>
              <span className="text-xs text-gray-400">Step 1 of 2</span>
            </div>

            {/* Quick Presets */}
            <div className="mb-4">
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Sample Commodity Presets
              </label>
              <div className="grid grid-cols-2 gap-2">
                {COMMODITY_PRESETS.map((p) => {
                  const selected = commodityCategory === p.id;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => applyPreset(p)}
                      className={`p-2.5 rounded-lg border text-left text-xs transition-all ${
                        selected
                          ? 'border-emerald-600 bg-emerald-50/70 text-emerald-950 font-semibold shadow-xs ring-1 ring-emerald-600'
                          : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="truncate">{p.label.split('/')[0]}</span>
                        {selected && <Check size={12} className="text-emerald-700 flex-shrink-0" />}
                      </div>
                      <span className="text-[10px] text-gray-400 block mt-0.5">{p.days}d target</span>
                    </button>
                  );
                })}
              </div>
              {activePreset && (
                <p className="text-[11px] text-gray-500 mt-2 bg-gray-50 p-2 rounded border border-gray-100">
                  <span className="font-semibold text-gray-700">Sensitivity: </span>
                  {activePreset.notes}
                </p>
              )}
            </div>

            {/* Shelf-Life Slider */}
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 mb-4">
              <div className="flex justify-between items-baseline mb-1">
                <label className="text-xs font-bold text-gray-800 uppercase tracking-wide">
                  Target Shelf Life
                </label>
                <div className="text-xl font-bold text-emerald-700">
                  {shelfLifeDays} <span className="text-xs font-normal text-gray-500">days</span>
                </div>
              </div>
              <input
                type="range"
                min="7"
                max="365"
                step="7"
                value={shelfLifeDays}
                onChange={(e) => setShelfLifeDays(Number(e.target.value))}
                className="w-full accent-emerald-600 h-2 bg-gray-200 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                <span>1 Week (Direct farm sale)</span>
                <span>4 Months (Domestic retail)</span>
                <span>1 Year (Export)</span>
              </div>
              <p className="text-[11px] text-gray-600 mt-2">
                Adjust this slider to see how shorter storage lets you use economical films without compromising product safety.
              </p>
            </div>

            {/* Pack Size */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Fill Weight (Grams per Unit)
              </label>
              <input
                type="number"
                value={packWeightGrams}
                onChange={(e) => setPackWeightGrams(Number(e.target.value))}
                className="w-full text-sm border-gray-300 rounded-lg p-2 border focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            {/* Editable Assumptions Accordion */}
            <div className="pt-2 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setShowAdvancedAssumptions(!showAdvancedAssumptions)}
                className="text-xs text-gray-600 hover:text-emerald-700 font-medium flex items-center gap-1.5"
              >
                <Info size={13} className="text-gray-400" />
                {showAdvancedAssumptions ? 'Hide food chemistry parameters' : 'Inspect or edit critical limits (moisture & fat)'}
              </button>

              {showAdvancedAssumptions && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-3 text-xs">
                  <div>
                    <label className="block text-gray-700 font-medium mb-0.5">
                      Critical Moisture Threshold for Spoilage (% w/w)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={criticalMoisture}
                      onChange={(e) => setCriticalMoisture(Number(e.target.value))}
                      className="w-full border border-gray-300 rounded p-1.5 bg-white"
                    />
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      Maximum moisture the product can absorb before crispness loss or mold occurs.
                    </p>
                  </div>
                  {commodityCategory === 'oily' && (
                    <div>
                      <label className="block text-gray-700 font-medium mb-0.5">
                        Fat Content in Food Formulation (%)
                      </label>
                      <input
                        type="number"
                        step="1"
                        value={fatPct}
                        onChange={(e) => setFatPct(Number(e.target.value))}
                        className="w-full border border-gray-300 rounded p-1.5 bg-white"
                      />
                      <p className="text-[10px] text-gray-400 mt-0.5">
                        Used to calculate allowable oxygen uptake before rancidity index exceeds 10 meq/kg.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Card: Transit & Climate Route */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                <MapPin size={16} className="text-blue-600" />
                Climate Zone & Transport Route
              </h2>
              <span className="text-xs text-gray-400">Step 2 of 2</span>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">
                  Destination / Storage Location
                </label>
                <select
                  value={cityName}
                  onChange={(e) => setCityName(e.target.value)}
                  className="w-full text-sm border-gray-300 rounded-lg p-2 border bg-gray-50"
                >
                  {climateOptions?.cities &&
                    Object.keys(climateOptions.cities).map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-gray-700 mb-1">
                    Season
                  </label>
                  <select
                    value={season}
                    onChange={(e) => setSeason(e.target.value)}
                    className="w-full text-xs border-gray-300 rounded-lg p-2 border bg-gray-50"
                  >
                    <option value="standard">Standard Ambient</option>
                    <option value="monsoon">Monsoon (&gt;85% RH)</option>
                    <option value="peak_summer">Peak Summer (&gt;40°C)</option>
                    <option value="winter">Dry Winter</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-gray-700 mb-1">
                    Transport Mode
                  </label>
                  <select
                    value={transitMode}
                    onChange={(e) => setTransitMode(e.target.value)}
                    className="w-full text-xs border-gray-300 rounded-lg p-2 border bg-gray-50"
                  >
                    <option value="truck_standard">Road Freight (Standard)</option>
                    <option value="rail_freight">Container Rail</option>
                    <option value="cold_chain_reefer">Chilled Reefer</option>
                    <option value="last_mile_2wheeler">Last-Mile 2-Wheeler</option>
                  </select>
                </div>
              </div>

              {/* Cold Chain Break Test */}
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold text-gray-800 flex items-center gap-1.5">
                    <Clock size={13} className="text-gray-500" />
                    Cold-Chain Interruption What-If:
                  </span>
                  <span className="font-bold text-gray-900">{coldChainBreakHours} hrs @ 35°C</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="12"
                  step="1"
                  value={coldChainBreakHours}
                  onChange={(e) => setColdChainBreakHours(Number(e.target.value))}
                  className="w-full accent-gray-700 h-1.5 bg-gray-200 rounded cursor-pointer"
                />
                <p className="text-[10px] text-gray-500 mt-1">
                  Accounts for ambient loading dock exposure or logistics transfer bottlenecks.
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: SPECS, PARETO PICKS, TRADE-OFFS */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* BARRIER TARGET CARD */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex flex-wrap justify-between items-baseline gap-2 mb-4 border-b pb-3">
              <div>
                <h3 className="text-lg font-bold text-gray-900">
                  Target Barrier Requirements
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Calculated based on {shelfLifeDays} days shelf-life in {cityName} ({season.replace('_', ' ')}).
                </p>
              </div>
              <EvidenceBadge type="Estimated" />
            </div>

            {loading ? (
              <LoadingSkeleton rows={4} />
            ) : solverResult?.solution ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  
                  {/* WVTR Card */}
                  <div className="border border-gray-200 rounded-xl p-4 bg-gray-50/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
                        Max Allowable WVTR
                      </span>
                      <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border text-gray-600">
                        ASTM F1249
                      </span>
                    </div>
                    <div className="text-3xl font-extrabold text-gray-900 mt-1">
                      ≤ {solverResult.solution.barrier_requirements.max_allowable_wvtr}
                      <span className="text-xs font-normal text-gray-500 ml-1.5">g/m²·day</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                      Film must block moisture so total water uptake stays below {criticalMoisture}%.
                    </p>
                  </div>

                  {/* OTR Card */}
                  <div className="border border-gray-200 rounded-xl p-4 bg-gray-50/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">
                        Max Allowable OTR
                      </span>
                      <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border text-gray-600">
                        ASTM D3985
                      </span>
                    </div>
                    <div className="text-3xl font-extrabold text-gray-900 mt-1">
                      ≤ {solverResult.solution.barrier_requirements.max_allowable_otr}
                      <span className="text-xs font-normal text-gray-500 ml-1.5">cc/m²·day</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                      Limits oxygen ingress to avoid rancidity before the {shelfLifeDays}-day deadline.
                    </p>
                  </div>
                </div>

                {/* Fresh Produce MAP Details (if relevant) */}
                {solverResult.solution.map_produce_details && (
                  <div className="bg-emerald-50/60 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-950">
                    <div className="font-semibold text-emerald-900 mb-1 flex items-center gap-1.5">
                      Modified Atmosphere Packaging (MAP) Specifications
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
                      <div className="bg-white p-2 rounded border border-emerald-100">
                        <div className="text-gray-400 text-[10px]">Q10 Rate Shift</div>
                        <div className="font-bold text-emerald-800">{solverResult.solution.map_produce_details.q10_multiplier}x baseline</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-emerald-100">
                        <div className="text-gray-400 text-[10px]">Micro-Perforations</div>
                        <div className="font-bold text-emerald-800">{solverResult.solution.map_produce_details.recommended_micro_perforations} holes / pack</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-emerald-100">
                        <div className="text-gray-400 text-[10px]">Equilibrium Target</div>
                        <div className="font-bold text-emerald-800">4% O₂ / 6% CO₂</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-emerald-100">
                        <div className="text-gray-400 text-[10px]">Condensation Risk</div>
                        <div className={`font-bold ${solverResult.solution.map_produce_details.condensation_risk === 'CRITICAL' ? 'text-red-600' : 'text-amber-600'}`}>
                          {solverResult.solution.map_produce_details.condensation_risk}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Footnote */}
                <div className="flex items-start gap-2 pt-2 text-xs text-gray-500">
                  <AlertTriangle size={14} className="text-amber-500 mt-0.5 flex-shrink-0" />
                  <span>
                    Values represent theoretical maximum limits. Always verify batch samples with certified ASTM test laboratories before commercial roll-out.
                  </span>
                </div>
              </div>
            ) : null}
          </div>

          {/* THREE BALANCED OPTIONS (PARETO) */}
          {solverResult?.pareto_picks && Object.keys(solverResult.pareto_picks).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <div className="mb-4">
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
                  Recommended Material Options
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Pre-filtered structures that meet your barrier thresholds, categorized by priority.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {solverResult.pareto_picks.best_performance && (
                  <OptionCard
                    title="Best Barrier Margin"
                    description="Safest for volatile conditions"
                    badgeClass="bg-blue-50 text-blue-700 border-blue-200"
                    item={solverResult.pareto_picks.best_performance}
                  />
                )}
                {solverResult.pareto_picks.lowest_cost && (
                  <OptionCard
                    title="Most Economical"
                    description="Lowest procurement cost"
                    badgeClass="bg-emerald-50 text-emerald-700 border-emerald-200"
                    item={solverResult.pareto_picks.lowest_cost}
                  />
                )}
                {solverResult.pareto_picks.most_sustainable && (
                  <OptionCard
                    title="Highest Sustainability"
                    description="Lowest environmental burden"
                    badgeClass="bg-purple-50 text-purple-700 border-purple-200"
                    item={solverResult.pareto_picks.most_sustainable}
                  />
                )}
              </div>
            </div>
          )}

          {/* DOWNGRADE IMPACT SIMULATOR */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex justify-between items-baseline mb-3">
              <div>
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingDown size={15} className="text-gray-500" />
                  Cost Reduction vs. Shelf-Life Trade-Off
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Simulate the impact of switching to lower-cost films on product freshness.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
              <div className="md:col-span-6 space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-gray-700 mb-1">
                    <span>Baseline Grade Tier:</span>
                    <span className="font-semibold text-gray-900">{currentCostIndex.toFixed(1)} / 5.0</span>
                  </div>
                  <input
                    type="range"
                    min="2.5"
                    max="5.0"
                    step="0.5"
                    value={currentCostIndex}
                    onChange={(e) => setCurrentCostIndex(Number(e.target.value))}
                    className="w-full accent-gray-700 h-1.5 bg-gray-200 rounded cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs text-gray-700 mb-1">
                    <span>Target Economical Tier:</span>
                    <span className="font-semibold text-emerald-700">{targetCostIndex.toFixed(1)} / 5.0</span>
                  </div>
                  <input
                    type="range"
                    min="1.0"
                    max={currentCostIndex}
                    step="0.2"
                    value={targetCostIndex}
                    onChange={(e) => setTargetCostIndex(Number(e.target.value))}
                    className="w-full accent-emerald-600 h-1.5 bg-gray-200 rounded cursor-pointer"
                  />
                </div>
              </div>

              <div className="md:col-span-6 bg-gray-50 rounded-xl p-4 border border-gray-200 text-xs">
                {downgradeResult ? (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Expected Shelf Life:</span>
                      <span className="font-bold text-gray-900">
                        {downgradeResult.new_shelf_life_days} days
                        <span className="text-xs text-red-600 font-medium ml-1">
                          (-{downgradeResult.days_lost} days)
                        </span>
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Shelf-Life Reduction:</span>
                      <span className="font-semibold text-red-700">
                        {downgradeResult.percent_shelf_life_lost}% shorter
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estimated Material Savings:</span>
                      <span className="font-semibold text-emerald-700">
                        ~{downgradeResult.cost_saved_percent}%
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-600 border-t border-gray-200 pt-2 leading-relaxed">
                      {downgradeResult.tradeoff_analysis}
                    </p>
                  </div>
                ) : (
                  <LoadingSkeleton rows={3} />
                )}
              </div>
            </div>
          </div>

          {/* VENDOR & FARMER SPECIFICATION SHEET */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex flex-wrap justify-between items-center gap-3 mb-4 border-b pb-3">
              <div>
                <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
                  <FileSpreadsheet size={16} className="text-gray-600" />
                  Supplier Procurement Summary
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Clear specifications for packaging suppliers and converter requests.
                </p>
              </div>

              <button
                type="button"
                onClick={speakPlainLanguage}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  speaking
                    ? 'bg-gray-800 text-white animate-pulse'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300'
                }`}
              >
                <Volume2 size={14} /> {speaking ? 'Playing audio...' : 'Audio Summary'}
              </button>
            </div>

            {/* Clean Spec Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="p-3 rounded-lg border border-gray-200 bg-gray-50 text-center">
                <div className="text-xs font-semibold text-gray-700">{t.moistureProtection}</div>
                <div className="text-sm font-bold text-gray-900 mt-1">
                  ≤ {solverResult?.solution?.barrier_requirements?.max_allowable_wvtr || 1.2}
                </div>
                <div className="text-[10px] text-gray-500">g/m²·day</div>
              </div>

              <div className="p-3 rounded-lg border border-gray-200 bg-gray-50 text-center">
                <div className="text-xs font-semibold text-gray-700">{t.oxygenProtection}</div>
                <div className="text-sm font-bold text-gray-900 mt-1">
                  ≤ {solverResult?.solution?.barrier_requirements?.max_allowable_otr || 15}
                </div>
                <div className="text-[10px] text-gray-500">cc/m²·day</div>
              </div>

              <div className="p-3 rounded-lg border border-gray-200 bg-gray-50 text-center">
                <div className="text-xs font-semibold text-gray-700">{t.thickness}</div>
                <div className="text-sm font-bold text-gray-900 mt-1">30 – 50</div>
                <div className="text-[10px] text-gray-500">microns (µm)</div>
              </div>

              <div className="p-3 rounded-lg border border-gray-200 bg-gray-50 text-center">
                <div className="text-xs font-semibold text-gray-700">{t.foodSafe}</div>
                <div className="text-sm font-bold text-emerald-700 mt-1">Compliant</div>
                <div className="text-[10px] text-gray-500">IS 9845 / 21 CFR</div>
              </div>
            </div>

            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700">
              <span className="font-semibold text-gray-900">Plain Language Guide: </span>
              {t.summaryText}
            </div>
          </div>

        </div>

      </div>
    </Layout>
  );
};

const OptionCard = ({ title, description, badgeClass, item }: any) => {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs flex flex-col justify-between hover:border-gray-300 transition-colors">
      <div>
        <div className="flex justify-between items-center mb-1.5">
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${badgeClass}`}>
            {title}
          </span>
          <span className="text-[11px] font-medium text-gray-500">Tier {item.cost_index}</span>
        </div>
        <h4 className="font-bold text-gray-900 text-sm leading-snug mb-1">{item.name}</h4>
        <p className="text-[11px] text-gray-400 mb-3">{description}</p>

        <div className="space-y-1 text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg border border-gray-100">
          <div className="flex justify-between">
            <span>WVTR:</span>
            <span className="font-medium text-gray-900">{item.wvtr} g/m²·d</span>
          </div>
          <div className="flex justify-between">
            <span>OTR:</span>
            <span className="font-medium text-gray-900">{item.otr} cc/m²·d</span>
          </div>
          <div className="flex justify-between">
            <span>Eco Score:</span>
            <span className="font-medium text-emerald-700">{item.sustainability_score}/100</span>
          </div>
        </div>
      </div>

      <div className="mt-3 pt-2 border-t border-gray-100 text-[10px] text-gray-500">
        <div className="text-emerald-700 font-medium">{item.sustainability_metrics?.summary}</div>
      </div>
    </div>
  );
};

export default InverseSolverPage;

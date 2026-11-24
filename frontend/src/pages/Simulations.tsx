import React, { useState } from 'react';
import api from '../services/api';
import {
  Sliders,
  Play,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  DollarSign
} from 'lucide-react';

export const Simulations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'supply_chain' | 'revenue'>('supply_chain');

  // Supply Chain state
  const [scDemandChange, setScDemandChange] = useState<number>(25);
  const [scSupplierDelay, setScSupplierDelay] = useState<number>(7);
  const [scInventoryReduction, setScInventoryReduction] = useState<number>(20);
  const [scLoading, setScLoading] = useState<boolean>(false);
  const [scResult, setScResult] = useState<any | null>(null);

  // Revenue state
  const [revChurnRate, setRevChurnRate] = useState<number>(15);
  const [revAovChange, setRevAovChange] = useState<number>(10);
  const [revRetentionBoost, setRevRetentionBoost] = useState<number>(5);
  const [revLoading, setRevLoading] = useState<boolean>(false);
  const [revResult, setRevResult] = useState<any | null>(null);

  const runScSimulation = async () => {
    try {
      setScLoading(true);
      const res = await api.post('/supply-chain/simulate', {
        demand_change_pct: scDemandChange,
        supplier_delay_days: scSupplierDelay,
        inventory_reduction_pct: -Math.abs(scInventoryReduction),
      });
      setScResult(res.data);
    } catch (err: any) {
      alert(`Simulation failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setScLoading(false);
    }
  };

  const runRevSimulation = async () => {
    try {
      setRevLoading(true);
      const res = await api.post('/revenue/simulate', {
        high_value_churn_pct: revChurnRate,
        aov_change_pct: revAovChange,
        retention_improvement_pct: revRetentionBoost,
      });
      setRevResult(res.data);
    } catch (err: any) {
      alert(`Simulation failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setRevLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">What-If Business Simulation Studio</h1>
        <p className="text-sm text-slate-500 mt-1">
          Stress-test operational capacity, supply chain disruptions, and revenue elasticity before making capital decisions.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('supply_chain')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'supply_chain'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Supply Chain Shock Simulator
          </button>
          <button
            onClick={() => setActiveTab('revenue')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'revenue'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Revenue & Churn Elasticity Simulator
          </button>
        </nav>
      </div>

      {/* Simulation Content */}
      {activeTab === 'supply_chain' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Panel */}
          <div className="lg:col-span-5 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center space-x-2 border-b pb-3 border-slate-100">
              <Sliders className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">Scenario Parameter Controls</h2>
            </div>

            {/* Slider 1: Demand Change */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Projected Demand Surge / Drop</span>
                <span className="text-indigo-600 font-bold">{scDemandChange > 0 ? `+${scDemandChange}%` : `${scDemandChange}%`}</span>
              </div>
              <input
                type="range"
                min="-50"
                max="100"
                step="5"
                value={scDemandChange}
                onChange={(e) => setScDemandChange(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>-50% Collapse</span>
                <span>0% Stable</span>
                <span>+100% Demand Surge</span>
              </div>
            </div>

            {/* Slider 2: Supplier Delay */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Supplier Delivery Delay (Lead Days)</span>
                <span className="text-amber-600 font-bold">+{scSupplierDelay} Days</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="1"
                value={scSupplierDelay}
                onChange={(e) => setScSupplierDelay(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>0 Days (On Time)</span>
                <span>15 Days</span>
                <span>30 Days Delay</span>
              </div>
            </div>

            {/* Slider 3: Inventory Reduction */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Sudden Inventory Loss / Damage</span>
                <span className="text-rose-600 font-bold">-{scInventoryReduction}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="80"
                step="5"
                value={scInventoryReduction}
                onChange={(e) => setScInventoryReduction(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>0% Loss</span>
                <span>40% Loss</span>
                <span>80% Loss</span>
              </div>
            </div>

            <button
              onClick={runScSimulation}
              disabled={scLoading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              <span>{scLoading ? 'Simulating Model...' : 'Execute What-If Simulation'}</span>
            </button>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-7 space-y-6">
            {scResult ? (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
                <div className="flex items-center justify-between border-b pb-3 border-slate-100">
                  <h3 className="text-lg font-bold text-slate-900">Simulation Outcome & Impact Analysis</h3>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
                    Est. Loss: ${scResult.estimated_financial_loss.toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-xs text-slate-500 block">Baseline Stock</span>
                    <span className="text-lg font-bold text-slate-900">{scResult.baseline_available_stock}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-xs text-slate-500 block">Simulated Stock</span>
                    <span className="text-lg font-bold text-amber-600">{scResult.simulated_available_stock}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-xs text-slate-500 block">Simulated Demand</span>
                    <span className="text-lg font-bold text-indigo-600">{scResult.simulated_expected_demand.toFixed(0)}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-xs text-slate-500 block">Shortage Units</span>
                    <span className="text-lg font-bold text-rose-600">{scResult.potential_shortage_units.toFixed(0)}</span>
                  </div>
                </div>

                <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-xl space-y-2">
                  <div className="flex items-center space-x-2 text-amber-900 font-semibold text-xs uppercase tracking-wider">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Prescriptive Action Recommended</span>
                  </div>
                  <p className="text-sm text-slate-800 font-medium">{scResult.recommended_action}</p>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl text-xs text-slate-600 space-y-1">
                  <span className="font-semibold text-slate-800 block">Simulation Model Assumptions:</span>
                  <p className="leading-relaxed">{scResult.assumptions_summary}</p>
                </div>
              </div>
            ) : (
              <div className="h-full min-h-[300px] flex flex-col items-center justify-center bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
                <Layers className="w-12 h-12 text-slate-400 mb-3 opacity-60" />
                <h3 className="font-semibold text-slate-700">No Simulation Run Yet</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Adjust the scenario parameters on the left and click "Execute What-If Simulation" to project supply chain stockout risks and financial loss.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Revenue Simulation */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Panel */}
          <div className="lg:col-span-5 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center space-x-2 border-b pb-3 border-slate-100">
              <Sliders className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">Revenue Elasticity Controls</h2>
            </div>

            {/* Slider 1: Churn Rate */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">High-Value Customer Churn</span>
                <span className="text-rose-600 font-bold">{revChurnRate}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={revChurnRate}
                onChange={(e) => setRevChurnRate(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>0% Churn</span>
                <span>25% Churn</span>
                <span>50% Catastrophic</span>
              </div>
            </div>

            {/* Slider 2: AOV Change */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Average Order Value (AOV) Adjustment</span>
                <span className="text-indigo-600 font-bold">{revAovChange > 0 ? `+${revAovChange}%` : `${revAovChange}%`}</span>
              </div>
              <input
                type="range"
                min="-30"
                max="50"
                step="5"
                value={revAovChange}
                onChange={(e) => setRevAovChange(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>-30% Price Drop</span>
                <span>0% Unchanged</span>
                <span>+50% Upsell</span>
              </div>
            </div>

            {/* Slider 3: Retention Boost */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-700">Targeted Retention Campaign Lift</span>
                <span className="text-emerald-600 font-bold">+{revRetentionBoost}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="40"
                step="5"
                value={revRetentionBoost}
                onChange={(e) => setRevRetentionBoost(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>0% No Campaign</span>
                <span>20% Lift</span>
                <span>+40% High Lift</span>
              </div>
            </div>

            <button
              onClick={runRevSimulation}
              disabled={revLoading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              <span>{revLoading ? 'Simulating Financials...' : 'Simulate Revenue Impact'}</span>
            </button>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-7 space-y-6">
            {revResult ? (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
                <div className="flex items-center justify-between border-b pb-3 border-slate-100">
                  <h3 className="text-lg font-bold text-slate-900">Projected Cashflow Impact</h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    revResult.revenue_difference >= 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                  }`}>
                    {revResult.revenue_difference >= 0 ? '+' : ''}${revResult.revenue_difference.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({revResult.percentage_impact.toFixed(1)}%)
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-xs text-slate-500 block">Baseline Expected Revenue</span>
                    <span className="text-2xl font-bold text-slate-900">
                      ${revResult.baseline_expected_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-xs text-slate-500 block">Simulated Outcome</span>
                    <span className={`text-2xl font-bold ${revResult.revenue_difference >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      ${revResult.simulated_expected_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-2">
                  <div className="flex items-center space-x-2 text-emerald-900 font-semibold text-xs uppercase tracking-wider">
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    <span>Recovery & Growth Opportunity</span>
                  </div>
                  <p className="text-sm text-slate-800 font-medium">{revResult.potential_recovery_opportunities}</p>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl text-xs text-slate-600 space-y-1">
                  <span className="font-semibold text-slate-800 block">Simulation Model Assumptions:</span>
                  <p className="leading-relaxed">{revResult.assumptions_summary}</p>
                </div>
              </div>
            ) : (
              <div className="h-full min-h-[300px] flex flex-col items-center justify-center bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
                <DollarSign className="w-12 h-12 text-slate-400 mb-3 opacity-60" />
                <h3 className="font-semibold text-slate-700">No Revenue Simulation Run Yet</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Adjust churn and AOV parameters on the left to project financial gains or losses.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Simulations;


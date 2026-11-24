import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Truck,
  Users,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  ChevronUp,
  ChevronDown,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';

export const Overview: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [revenueData, setRevenueData] = useState<any>(null);
  const [inventoryOverview, setInventoryOverview] = useState<any>(null);
  const [supplierCards, setSupplierCards] = useState<any[]>([]);
  const [churnRisks, setChurnRisks] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [showGuide, setShowGuide] = useState<boolean>(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [revRes, invRes, suppRes, churnRes, recRes] = await Promise.allSettled([
        api.get('/revenue/overview'),
        api.get('/supply-chain/inventory'),
        api.get('/supply-chain/suppliers'),
        api.get('/revenue/churn'),
        api.get('/recommendations?status=PENDING'),
      ]);

      if (revRes.status === 'fulfilled') setRevenueData(revRes.value.data);
      if (invRes.status === 'fulfilled') setInventoryOverview(invRes.value.data);
      if (suppRes.status === 'fulfilled') setSupplierCards(suppRes.value.data);
      if (churnRes.status === 'fulfilled') setChurnRisks(churnRes.value.data);
      if (recRes.status === 'fulfilled') setRecommendations(recRes.value.data);
    } catch (e) {
      console.error('Failed to load dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const totalRev = revenueData?.total_revenue || 0;
  const growthRate = revenueData?.monthly_growth_rate || 0;
  const productsAtRisk = inventoryOverview?.critical_shortage_count || 0;
  const supplierAlerts = supplierCards.filter((s) => s.risk_level === 'CRITICAL' || s.risk_level === 'HIGH').length;
  const highChurnCount = churnRisks.filter((c) => c.risk_category === 'CRITICAL' || c.risk_category === 'HIGH').length;
  const pendingRecsCount = recommendations.length;

  return (
    <div className="space-y-8">
      {/* Top Welcome & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Intelligence Overview</h1>
          <p className="text-sm text-slate-600 mt-1">
            Real-time cross-domain analytics, predictive risk monitors, and decision triggers.
          </p>
        </div>
        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition-colors shadow-sm self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          Refresh Insights
        </button>
      </div>

      {/* Step-by-Step Onboarding Guide */}
      {showGuide && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs font-bold border border-indigo-200">
                ?
              </span>
              <div>
                <h2 className="text-sm font-bold text-slate-900">Quick Start: How to Use BusinessPulse AI (Step by Step)</h2>
                <p className="text-xs text-slate-500">Follow these 3 steps to turn raw CSV/Excel files into live forecasts and business decisions.</p>
              </div>
            </div>
            <button
              onClick={() => setShowGuide(false)}
              className="text-xs font-medium text-slate-500 hover:text-slate-700"
            >
              Hide
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Step 1 · Upload & Check</span>
                  {totalRev > 0 && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1">Ingest Your Dataset</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Select a schema (e.g. <strong>Sales Transactions</strong>), choose your CSV/Excel file, click <strong>Dry-Run Validation Preview</strong> to catch errors, then click <strong>Confirm & Commit Ingestion</strong>.
                </p>
              </div>
              <Link
                to="/data-sources"
                className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline"
              >
                Go to Data Sources <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Step 2 · Run AI Analytics</span>
                  {totalRev > 0 && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1">Explore Forecasts & Risks</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Open <strong>SupplyChain</strong> or <strong>Revenue Intelligence</strong> and click <strong>Re-run ML Forecaster / Pipeline</strong> to compute demand, stockouts, churn risk, and customer segments.
                </p>
              </div>
              <div className="mt-3 flex items-center gap-4">
                <Link to="/supply-chain" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  SupplyChain <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link to="/revenue" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  Revenue <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Step 3 · Decide & Simulate</span>
                  {pendingRecsCount > 0 && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1">Approve or Stress-Test</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Click <strong>Run Decision Engine</strong> in <strong>Recommendations</strong>, review &amp; approve actions in <strong>Approval Center</strong>, or test scenarios in <strong>What-If Simulations</strong>.
                </p>
              </div>
              <div className="mt-3 flex items-center gap-4">
                <Link to="/recommendations" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  Recommendations <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link to="/simulations" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  Simulations <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Total Revenue */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Revenue</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">${totalRev.toLocaleString()}</div>
            <div className="text-xs text-slate-500 mt-1">
              AOV: ${revenueData?.average_order_value?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>

        {/* Revenue Growth */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Monthly Growth</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 flex items-center gap-1">
              {growthRate >= 0 ? '+' : ''}{growthRate.toFixed(1)}%
              {growthRate >= 0 ? (
                <ArrowUpRight className="w-4 h-4 text-emerald-600" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-rose-600" />
              )}
            </div>
            <div className="text-xs text-slate-500 mt-1">vs Prior 30 Days</div>
          </div>
        </div>

        {/* Products at Risk */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Stock Shortages</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{productsAtRisk}</div>
            <div className="text-xs text-amber-600 mt-1 font-medium">Critical Inventory</div>
          </div>
        </div>

        {/* Supplier Alerts */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Supplier Risks</span>
            <Truck className="w-4 h-4 text-rose-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{supplierAlerts}</div>
            <div className="text-xs text-slate-500 mt-1">SLA Delivery Concerns</div>
          </div>
        </div>

        {/* Churn Risk */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">At-Risk Clients</span>
            <Users className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{highChurnCount}</div>
            <div className="text-xs text-purple-600 mt-1 font-medium">High Churn Probability</div>
          </div>
        </div>

        {/* Pending Decisions */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Pending Decisions</span>
            <Lightbulb className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{pendingRecsCount}</div>
            <div className="text-xs text-indigo-600 mt-1 font-medium">Require Approval</div>
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Trends Chart */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-slate-900">Monthly Revenue Velocity</h2>
              <p className="text-xs text-slate-500 mt-0.5">Historical revenue and transaction trajectories</p>
            </div>
          </div>

          <div className="h-72 w-full">
            {revenueData?.historical_monthly_trend && revenueData.historical_monthly_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={revenueData.historical_monthly_trend}>
                  <defs>
                    <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.2} />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} tickFormatter={(val) => `$${val}`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                    itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No revenue history available. Ingest transaction datasets to render trend.
              </div>
            )}
          </div>
        </div>

        {/* Priority Action Alerts */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900">Critical Alerts</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 border border-rose-200">
                Action Required
              </span>
            </div>

            <div className="space-y-3">
              {recommendations.slice(0, 3).map((rec) => (
                <div key={rec.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 hover:border-indigo-300 transition-colors">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                      {rec.module}
                    </span>
                    <span className="text-xs font-bold text-emerald-600">
                      ${Number(rec.expected_financial_impact).toLocaleString()} exp
                    </span>
                  </div>
                  <h3 className="text-xs font-semibold text-slate-900 truncate">{rec.title}</h3>
                  <p className="text-[11px] text-slate-600 line-clamp-2 mt-1">{rec.description}</p>
                </div>
              ))}

              {recommendations.length === 0 && (
                <div className="text-center py-12 text-slate-500 text-xs">
                  No pending critical alerts. All policies within nominal bounds.
                </div>
              )}
            </div>
          </div>

          <a
            href="/recommendations"
            className="w-full mt-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm"
          >
            Open Recommendation Center
          </a>
        </div>
      </div>
    </div>
  );
};


import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  AlertCircle,
  RefreshCw,
  PieChart as PieIcon,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar
} from 'recharts';

interface RevenueOverview {
  total_revenue: number;
  current_month_revenue: number;
  previous_month_revenue: number;
  monthly_growth_rate: number;
  average_order_value: number;
  total_transactions: number;
  historical_monthly_trend: Array<{ month: string; revenue: number; orders: number }>;
}

interface ForecastDailyItem {
  date: string;
  predicted_revenue: number;
  lower_bound: number;
  upper_bound: number;
}

interface RevenueForecastData {
  organization_id: string;
  forecasts: Record<string, {
    horizon_days: number;
    total_predicted_revenue: number;
    daily_average: number;
    daily_breakdown: ForecastDailyItem[];
  }>;
  metrics: {
    wape?: number;
    mae?: number;
    rmse?: number;
  };
  beats_baseline: boolean;
  generated_at: string;
}

interface ChurnCustomer {
  customer_id: string;
  customer_code: string;
  name: string;
  email: string | null;
  churn_probability: number;
  risk_category: string;
  monetary_value: number;
  recency_days: number;
  velocity_slope: number;
  contributing_features: Record<string, any>;
}

interface CustomerSegment {
  segment_name: string;
  customer_count: number;
  total_revenue: number;
  average_spend: number;
  revenue_contribution_pct: number;
}

export const Revenue: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'forecast' | 'churn' | 'segments'>('forecast');
  const [loading, setLoading] = useState<boolean>(true);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [overview, setOverview] = useState<RevenueOverview | null>(null);
  const [forecast, setForecast] = useState<RevenueForecastData | null>(null);
  const [churnList, setChurnList] = useState<ChurnCustomer[]>([]);
  const [segments, setSegments] = useState<CustomerSegment[]>([]);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchRevenueData = async () => {
    try {
      setLoading(true);
      const [overRes, foreRes, churnRes, segRes] = await Promise.all([
        api.get('/revenue/overview'),
        api.get('/revenue/forecast'),
        api.get('/revenue/churn'),
        api.get('/revenue/segments'),
      ]);
      setOverview(overRes.data);
      setForecast(foreRes.data);
      setChurnList(churnRes.data);
      setSegments(segRes.data);
    } catch (err: any) {
      console.error('Failed to load revenue intelligence data', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerForecastPipeline = async () => {
    try {
      setTriggering(true);
      setNotification('Running Revenue Forecasting & Churn ML Pipelines...');
      const res = await api.post('/revenue/forecast/trigger');
      setNotification(`Forecast updated! 30-day projection: $${res.data.forecast_30d_total?.toLocaleString()}. Beats 30d MA: ${res.data.beats_baseline ? 'Yes' : 'Evaluated'}.`);
      await fetchRevenueData();
      setTimeout(() => setNotification(null), 6000);
    } catch (err: any) {
      setNotification('Error triggering revenue forecast pipeline.');
      setTimeout(() => setNotification(null), 5000);
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchRevenueData();
  }, []);

  const getRiskBadge = (category: string) => {
    switch (category.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800">Critical Churn Risk</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">High Risk</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">Moderate</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Low Risk</span>;
    }
  };

  const forecast30 = forecast?.forecasts['30_days'] || forecast?.forecasts['30d'];
  const forecastBreakdown = forecast30?.daily_breakdown || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Revenue Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Predictive cashflow forecasts with confidence bounds, XGBoost churn classification, and RFM customer segmentation.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={triggerForecastPipeline}
            disabled={triggering}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${triggering ? 'animate-spin' : ''}`} />
            {triggering ? 'Computing Predictions...' : 'Re-run ML Pipeline'}
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-900 text-sm flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-indigo-600 font-semibold hover:underline">Dismiss</button>
        </div>
      )}

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Revenue</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">
              ${(overview?.total_revenue || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </h3>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Monthly Growth</p>
            <div className="flex items-center space-x-2 mt-1">
              <h3 className={`text-2xl font-bold ${(overview?.monthly_growth_rate || 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {(overview?.monthly_growth_rate || 0) >= 0 ? '+' : ''}{(overview?.monthly_growth_rate || 0).toFixed(1)}%
              </h3>
              {(overview?.monthly_growth_rate || 0) >= 0 ? (
                <ArrowUpRight className="w-5 h-5 text-emerald-600" />
              ) : (
                <ArrowDownRight className="w-5 h-5 text-rose-600" />
              )}
            </div>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Avg Order Value</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">
              ${(overview?.average_order_value || 0).toFixed(2)}
            </h3>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">High Churn Customers</p>
            <h3 className="text-2xl font-bold text-rose-600 mt-1">
              {churnList.filter((c) => c.risk_category === 'CRITICAL' || c.risk_category === 'HIGH').length}
            </h3>
          </div>
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <AlertCircle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('forecast')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'forecast'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            30-Day Predictive Revenue & Confidence Bounds
          </button>
          <button
            onClick={() => setActiveTab('churn')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'churn'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Customer Churn Risk Radar ({churnList.length})
          </button>
          <button
            onClick={() => setActiveTab('segments')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'segments'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            K-Means RFM Customer Segments
          </button>
        </nav>
      </div>

      {/* Tab 1: Revenue Forecast */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">30-Day Cashflow Revenue Forecast</h3>
                <p className="text-xs text-slate-500">
                  Model: XGBoost Regressor with 95% Confidence Bounds | WAPE: {(forecast?.metrics?.wape || 0).toFixed(3)} | MAE: ${(forecast?.metrics?.mae || 0).toFixed(0)} | Beats Baseline: {forecast?.beats_baseline ? 'Yes' : 'Evaluated'}
                </p>
              </div>
              <div className="flex space-x-6">
                <div className="text-right">
                  <span className="text-xs text-slate-500">Total 30D Forecast</span>
                  <p className="text-2xl font-bold text-emerald-600">
                    ${(forecast30?.total_predicted_revenue || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                </div>
                <div className="text-right border-l pl-6 border-slate-200">
                  <span className="text-xs text-slate-500">Predicted Daily Avg</span>
                  <p className="text-2xl font-bold text-slate-900">
                    ${(forecast30?.daily_average || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                </div>
              </div>
            </div>

            {/* Confidence Bounds Chart */}
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastBreakdown} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="revenueBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(val) => `$${val}`} />
                  <Tooltip 
                    formatter={(val: number) => [`$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, '']}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="upper_bound"
                    name="95% Upper Bound"
                    stroke="#059669"
                    strokeDasharray="4 4"
                    fill="url(#revenueBand)"
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted_revenue"
                    name="Predicted Daily Revenue"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="lower_bound"
                    name="95% Lower Bound"
                    stroke="#047857"
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Churn Radar */}
      {activeTab === 'churn' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Predictive Customer Churn Classifier</h2>
              <p className="text-xs text-slate-500 mt-0.5">Ranked by churn likelihood and purchasing velocity decline</p>
            </div>
            <span className="text-xs text-slate-500">{churnList.length} accounts analyzed</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Customer</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Churn Probability</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Risk Category</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Lifetime Spend</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Recency (Days)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Velocity Slope</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {churnList.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500 text-sm">
                      No churn risks detected.
                    </td>
                  </tr>
                ) : (
                  churnList.map((customer) => (
                    <tr key={customer.customer_id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-slate-900">{customer.name}</div>
                        <div className="text-xs text-slate-500">{customer.customer_code} • {customer.email || 'No email'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="inline-flex items-center space-x-2">
                          <div className="w-16 bg-slate-100 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${customer.churn_probability > 0.6 ? 'bg-rose-500' : customer.churn_probability > 0.3 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.round(customer.churn_probability * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs font-bold text-slate-800">
                            {(customer.churn_probability * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {getRiskBadge(customer.risk_category)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-slate-900">
                        ${customer.monetary_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-600">
                        {customer.recency_days} days ago
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold">
                        <span className={customer.velocity_slope < 0 ? 'text-rose-600' : 'text-emerald-600'}>
                          {customer.velocity_slope.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Customer Segments */}
      {activeTab === 'segments' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {segments.map((seg) => (
              <div key={seg.segment_name} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900">{seg.segment_name}</h3>
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700">
                    {seg.revenue_contribution_pct.toFixed(1)}% Revenue
                  </span>
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{seg.customer_count}</p>
                  <p className="text-xs text-slate-500">Customers in cluster</p>
                </div>
                <div className="pt-2 border-t border-slate-100 flex justify-between text-xs text-slate-600">
                  <span>Total Value:</span>
                  <span className="font-semibold text-slate-900">${seg.total_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-600">
                  <span>Avg Spend:</span>
                  <span className="font-semibold text-slate-900">${seg.average_spend.toFixed(0)}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4">Segment Revenue Contribution</h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={segments} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="segment_name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(val) => `$${val}`} />
                  <Tooltip formatter={(val: number) => [`$${val.toLocaleString()}`, 'Total Segment Revenue']} />
                  <Bar dataKey="total_revenue" name="Total Revenue" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Revenue;

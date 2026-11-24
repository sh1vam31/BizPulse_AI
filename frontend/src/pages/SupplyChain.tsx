import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { 
  Package, 
  AlertTriangle, 
  TrendingUp, 
  Truck, 
  RefreshCw, 
  ShieldAlert, 
  CheckCircle2, 
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface InventoryItem {
  product_id: string;
  sku: string;
  product_name: string;
  category: string;
  available_stock: number;
  reserved_stock: number;
  reorder_threshold: number;
  safety_stock: number;
  stock_status: string;
  unit_cost: number;
  total_value: number;
}

interface InventoryOverview {
  total_products: number;
  total_inventory_value: number;
  low_stock_products_count: number;
  critical_shortage_count: number;
  items: InventoryItem[];
}

interface InventoryRisk {
  product_id: string;
  sku: string;
  product_name: string;
  available_stock: number;
  safety_stock: number;
  expected_14d_demand: number;
  expected_shortage: number;
  days_of_stock_left: number;
  expected_stockout_date: string | null;
  risk_level: string;
  recommended_replenishment_quantity: number;
}

interface SupplierScorecard {
  supplier_id: string;
  supplier_code: string;
  name: string;
  reliability_score: number;
  average_lead_days: number;
  total_orders: number;
  delayed_orders: number;
  on_time_delivery_rate: number;
  risk_level: string;
}

interface ForecastHorizon {
  horizon_days: number;
  total_demand: number;
  daily_average: number;
  daily_breakdown: Array<{ date: string; predicted_demand: number; day_of_week?: number }>;
}

interface ProductForecast {
  product_id: string;
  sku: string;
  product_name: string;
  forecasts: Record<string, ForecastHorizon>;
  metrics: {
    wape?: number;
    mae?: number;
    rmse?: number;
  };
  beats_baseline: boolean;
  generated_at: string;
}

export const SupplyChain: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'forecast' | 'risks' | 'suppliers'>('overview');
  const [loading, setLoading] = useState<boolean>(true);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [overview, setOverview] = useState<InventoryOverview | null>(null);
  const [risks, setRisks] = useState<InventoryRisk[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierScorecard[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [selectedHorizon, setSelectedHorizon] = useState<string>('14d');
  const [productForecast, setProductForecast] = useState<ProductForecast | null>(null);
  const [forecastLoading, setForecastLoading] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchBaseData = async () => {
    try {
      setLoading(true);
      const [invRes, riskRes, supRes] = await Promise.all([
        api.get('/supply-chain/inventory'),
        api.get('/supply-chain/risks'),
        api.get('/supply-chain/suppliers'),
      ]);
      setOverview(invRes.data);
      setRisks(riskRes.data);
      setSuppliers(supRes.data);

      if (invRes.data.items && invRes.data.items.length > 0 && !selectedProductId) {
        setSelectedProductId(invRes.data.items[0].product_id);
      }
    } catch (err: any) {
      console.error('Failed to load supply chain data', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchForecast = async (productId: string) => {
    if (!productId) return;
    try {
      setForecastLoading(true);
      const res = await api.get(`/supply-chain/forecast?product_id=${productId}`);
      setProductForecast(res.data);
    } catch (err: any) {
      console.error('Failed to fetch demand forecast', err);
      setProductForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  const triggerForecastPipeline = async () => {
    if (!selectedProductId) {
      setNotification('Please select a product first to run the ML forecaster.');
      setTimeout(() => setNotification(null), 4000);
      return;
    }
    try {
      setTriggering(true);
      setNotification('Running ML Demand Forecasting Pipeline...');
      const res = await api.post('/supply-chain/forecast/trigger', null, {
        params: { product_id: selectedProductId },
      });
      setNotification(`Forecast pipeline completed (${res.data.forecasts?.length || 0} horizon periods). Baseline beaten: ${res.data.beats_baseline ? 'Yes' : 'No'}.`);
      await fetchBaseData();
      await fetchForecast(selectedProductId);
      setTimeout(() => setNotification(null), 6000);
    } catch (err: any) {
      setNotification('Error triggering forecast pipeline.');
      setTimeout(() => setNotification(null), 5000);
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchBaseData();
  }, []);

  useEffect(() => {
    if (selectedProductId) {
      fetchForecast(selectedProductId);
    }
  }, [selectedProductId]);

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800">Critical</span>;
      case 'LOW_STOCK':
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">Low Stock / High Risk</span>;
      case 'OVERSTOCKED':
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">Overstocked / Med</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Healthy / Low</span>;
    }
  };

  const currentHorizonData = productForecast?.forecasts[selectedHorizon];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">SupplyChain Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time inventory levels, multi-horizon ML demand forecasts, and supplier reliability risks.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={triggerForecastPipeline}
            disabled={triggering}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${triggering ? 'animate-spin' : ''}`} />
            {triggering ? 'Forecasting...' : 'Re-run ML Forecaster'}
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-900 text-sm flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-indigo-600 font-semibold hover:underline">Dismiss</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Products</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{overview?.total_products || 0}</h3>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Package className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Inventory Value</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">
              ${(overview?.total_inventory_value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </h3>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Low Stock SKUs</p>
            <h3 className="text-2xl font-bold text-amber-600 mt-1">{overview?.low_stock_products_count || 0}</h3>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Critical Stockouts</p>
            <h3 className="text-2xl font-bold text-rose-600 mt-1">{overview?.critical_shortage_count || 0}</h3>
          </div>
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Inventory Stocklist
          </button>
          <button
            onClick={() => setActiveTab('forecast')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'forecast'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            ML Demand Forecaster
          </button>
          <button
            onClick={() => setActiveTab('risks')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'risks'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Stockout Risks & Depletion ({risks.length})
          </button>
          <button
            onClick={() => setActiveTab('suppliers')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'suppliers'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Supplier Reliability Scorecards
          </button>
        </nav>
      </div>

      {/* Tab 1: Inventory Stocklist */}
      {activeTab === 'overview' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">Current Warehouse Stock Inventory</h2>
            <span className="text-xs text-slate-500">{overview?.items?.length || 0} items monitored</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Product / SKU</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Available Stock</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Safety Stock</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Reorder Level</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Value</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {overview?.items?.map((item) => (
                  <tr key={item.product_id} className="hover:bg-slate-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-slate-900">{item.product_name}</div>
                      <div className="text-xs text-slate-500">{item.sku}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{item.category}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-slate-900">{item.available_stock}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-500">{item.safety_stock}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-500">{item.reorder_threshold}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">{getStatusBadge(item.stock_status)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-slate-900">
                      ${item.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Demand Forecaster */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <label className="text-sm font-medium text-slate-700 whitespace-nowrap">Select Product:</label>
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                className="w-full sm:w-72 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {overview?.items?.map((item) => (
                  <option key={item.product_id} value={item.product_id}>
                    {item.product_name} ({item.sku})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-slate-500">Forecast Horizon:</span>
              {(['7d', '14d', '30d'] as const).map((h) => (
                <button
                  key={h}
                  onClick={() => setSelectedHorizon(h)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    selectedHorizon === h
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {h.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {forecastLoading ? (
            <div className="h-64 flex items-center justify-center bg-white rounded-xl border border-slate-200">
              <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
          ) : productForecast && currentHorizonData ? (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{productForecast.product_name}</h3>
                  <p className="text-xs text-slate-500">
                    Model: XGBoost Multi-Horizon Forecaster | WAPE: {(productForecast.metrics.wape || 0).toFixed(3)} | Beats Baseline: {productForecast.beats_baseline ? 'Yes (Seasonal Naive Surpassed)' : 'Baseline Evaluated'}
                  </p>
                </div>
                <div className="flex space-x-4">
                  <div className="text-right">
                    <span className="text-xs text-slate-500">Total Horizon Demand</span>
                    <p className="text-xl font-bold text-indigo-600">{currentHorizonData.total_demand.toFixed(0)} units</p>
                  </div>
                  <div className="text-right border-l pl-4 border-slate-200">
                    <span className="text-xs text-slate-500">Daily Average</span>
                    <p className="text-xl font-bold text-slate-900">{currentHorizonData.daily_average.toFixed(1)} / day</p>
                  </div>
                </div>
              </div>

              {/* Forecast Area Chart */}
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={currentHorizonData.daily_breakdown} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="demandGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip 
                      formatter={(val: number) => [`${val.toFixed(1)} units`, 'Predicted Demand']}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="predicted_demand" 
                      name="Predicted Demand" 
                      stroke="#4f46e5" 
                      fillOpacity={1} 
                      fill="url(#demandGrad)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-500">
              No forecast generated yet for this SKU. Click "Re-run ML Forecaster" above.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Stockout Risks */}
      {activeTab === 'risks' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Inventory Shortage & Stockout Prediction</h2>
              <p className="text-xs text-slate-500 mt-0.5">Calculated using 14-day demand forecast vs available inventory</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Available Stock</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Expected 14D Demand</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Expected Shortage</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Days of Stock</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Est. Stockout Date</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Risk Level</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Replenish Qty</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {risks.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-slate-500 text-sm">
                      No stockout risks detected. All inventory healthy!
                    </td>
                  </tr>
                ) : (
                  risks.map((risk) => (
                    <tr key={risk.product_id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-slate-900">{risk.product_name}</div>
                        <div className="text-xs text-slate-500">{risk.sku}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-slate-900">{risk.available_stock}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-600">{risk.expected_14d_demand.toFixed(0)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-rose-600">
                        {risk.expected_shortage > 0 ? `-${risk.expected_shortage.toFixed(0)}` : '0'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-slate-900">
                        {risk.days_of_stock_left.toFixed(1)} days
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-slate-600">
                        {risk.expected_stockout_date || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">{getStatusBadge(risk.risk_level)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-indigo-600">
                        +{risk.recommended_replenishment_quantity}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Suppliers */}
      {activeTab === 'suppliers' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {suppliers.map((sup) => (
            <div key={sup.supplier_id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-slate-900">{sup.name}</h3>
                  <p className="text-xs text-slate-500">{sup.supplier_code}</p>
                </div>
                {getStatusBadge(sup.risk_level)}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-500">Reliability Score:</span>
                  <span className="text-slate-900 font-bold">{sup.reliability_score.toFixed(1)} / 100</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${sup.reliability_score < 70 ? 'bg-rose-500' : sup.reliability_score < 85 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                    style={{ width: `${Math.min(100, sup.reliability_score)}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-center">
                <div>
                  <span className="text-xs text-slate-400 block">Avg Lead</span>
                  <span className="text-sm font-bold text-slate-800">{sup.average_lead_days}d</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">On-Time</span>
                  <span className="text-sm font-bold text-slate-800">{sup.on_time_delivery_rate.toFixed(0)}%</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Delayed</span>
                  <span className="text-sm font-bold text-rose-600">{sup.delayed_orders}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SupplyChain;


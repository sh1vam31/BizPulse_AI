import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Package,
  Users,
  Truck,
  Warehouse as WarehouseIcon,
  Search,
  RefreshCw,
  TrendingUp,
  DollarSign
} from 'lucide-react';

export const Entities: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'products' | 'customers' | 'suppliers' | 'warehouses'>('products');
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');

  const [products, setProducts] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);

  const fetchEntities = async () => {
    try {
      setLoading(true);
      const [prodRes, custRes, supRes, warRes] = await Promise.all([
        api.get('/entities/products', { params: { search: search || undefined } }),
        api.get('/entities/customers', { params: { search: search || undefined } }),
        api.get('/entities/suppliers', { params: { search: search || undefined } }),
        api.get('/entities/warehouses'),
      ]);
      setProducts(prodRes.data);
      setCustomers(custRes.data);
      setSuppliers(supRes.data);
      setWarehouses(warRes.data);
    } catch (err: any) {
      console.error('Failed to load entity data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntities();
  }, [search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Business Entity Directory</h1>
          <p className="text-sm text-slate-500 mt-1">
            Master records for products, customers, suppliers, and distribution warehouses with live performance aggregates.
          </p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, SKU, code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('products')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
              activeTab === 'products'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <Package className="w-4 h-4" />
            <span>Products ({products.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('customers')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
              activeTab === 'customers'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Customers ({customers.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('suppliers')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
              activeTab === 'suppliers'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <Truck className="w-4 h-4" />
            <span>Suppliers ({suppliers.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('warehouses')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
              activeTab === 'warehouses'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <WarehouseIcon className="w-4 h-4" />
            <span>Warehouses ({warehouses.length})</span>
          </button>
        </nav>
      </div>

      {/* Products Table */}
      {activeTab === 'products' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Product / SKU</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Category</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Unit Cost</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Selling Price</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Available Stock</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Total Sales Units</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Gross Revenue</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-900">{p.name}</div>
                      <div className="text-xs text-slate-500">{p.sku}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{p.category}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-600">${p.unit_cost.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-slate-900">${p.selling_price.toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-slate-800">{p.available_stock}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-600">{p.total_sales_quantity || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-emerald-600">
                      ${(p.total_revenue || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Customers Table */}
      {activeTab === 'customers' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Segment</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Total Orders</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Lifetime Spend</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Joined</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-900">{c.name}</div>
                      <div className="text-xs text-slate-500">{c.customer_code} • {c.email || 'No email'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700">
                        {c.current_segment}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-800">{c.total_orders || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-emerald-600">
                      ${(c.total_spend || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Suppliers Table */}
      {activeTab === 'suppliers' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Supplier</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase">Reliability Score</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Avg Lead Days</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Total Orders</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase">On-Time Rate</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {suppliers.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-900">{s.name}</div>
                      <div className="text-xs text-slate-500">{s.supplier_code} • {s.contact_email || 'No email'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className="font-bold text-slate-900">{s.reliability_score.toFixed(1)} / 100</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-800">{s.average_lead_days} days</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-800">{s.total_orders || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-emerald-600">
                      {(s.on_time_delivery_rate || 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Warehouses Table */}
      {activeTab === 'warehouses' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {warehouses.map((w) => (
            <div key={w.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center space-x-2">
                <WarehouseIcon className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900">{w.name}</h3>
              </div>
              <p className="text-xs text-slate-500">Location: {w.location}</p>
              <div className="pt-2 border-t border-slate-100 flex justify-between text-xs text-slate-600">
                <span>Total Stored Units:</span>
                <span className="font-bold text-slate-900">{w.total_quantity || 0}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Entities;


import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Truck,
  TrendingUp,
  Database,
  Building2,
  Lightbulb,
  CheckSquare,
  Sliders,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/supply-chain', label: 'SupplyChain Intelligence', icon: Truck },
  { to: '/revenue', label: 'Revenue Intelligence', icon: TrendingUp },
  { to: '/recommendations', label: 'Recommendations', icon: Lightbulb },
  { to: '/approvals', label: 'Approval Center', icon: CheckSquare },
  { to: '/simulations', label: 'What-If Simulations', icon: Sliders },
  { to: '/data-sources', label: 'Data Sources & Ingest', icon: Database },
  { to: '/entities', label: 'Business Entities', icon: Building2 },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-30">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
          BP
        </div>
        <div>
          <h1 className="font-bold text-base text-white tracking-tight">BusinessPulse AI</h1>
          <p className="text-xs text-slate-400">Predictive BI & Decisions</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};


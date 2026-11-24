import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { HowToUseModal } from './HowToUseModal';
import { LogOut, User as UserIcon, Shield, Sun, Moon, BookOpen } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [showHowToUse, setShowHowToUse] = useState(false);

  return (
    <>
      <header className="h-16 bg-white/95 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-20 transition-colors duration-200">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-600 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
            Organization
          </span>
          <span className="text-sm font-semibold text-slate-800">
            {user?.organization_id ? 'Enterprise Tenant' : 'Default Org'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowHowToUse(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-sm shadow-indigo-500/25 transition-colors"
            title="Step-by-step guide on how to use BusinessPulse AI"
          >
            <BookOpen className="w-4 h-4" />
            <span>How to Use</span>
          </button>

          <button
            onClick={toggleTheme}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span>Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-indigo-600" />
                <span>Dark</span>
              </>
            )}
          </button>

          {user && (
            <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
              <div className="text-right">
                <div className="text-sm font-semibold text-slate-900 leading-tight">{user.name}</div>
                <div className="text-xs text-indigo-600 flex items-center justify-end gap-1 font-medium">
                  <Shield className="w-3 h-3" />
                  {user.role}
                </div>
              </div>
              <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
                <UserIcon className="w-4 h-4" />
              </div>
            </div>
          )}

          <button
            onClick={logout}
            className="p-2 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      <HowToUseModal isOpen={showHowToUse} onClose={() => setShowHowToUse(false)} />
    </>
  );
};


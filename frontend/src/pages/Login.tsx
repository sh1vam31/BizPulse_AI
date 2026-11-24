import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, ArrowRight, Lock, Mail, User, Building } from 'lucide-react';

export const Login: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const extractErrorMessage = (err: any, fallback: string): string => {
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: any) => d?.msg || 'Invalid input').join(' • ');
    }
    if (detail && typeof detail === 'object') {
      return detail.msg || JSON.stringify(detail);
    }
    return err?.message || fallback;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (isRegister) {
        await register(name, email, password, orgName);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Authentication failed. Please check credentials.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setName('Demo Executive');
    setEmail('admin@acme.com');
    setPassword('AdminSecret123!');
    setIsSubmitting(true);
    try {
      await login('admin@acme.com', 'AdminSecret123!');
      navigate('/');
    } catch {
      // If admin doesn't exist, register demo user
      try {
        await register('Demo Executive', 'admin@acme.com', 'AdminSecret123!', 'Acme Corp');
        navigate('/');
      } catch (err: any) {
        setError(extractErrorMessage(err, 'Demo login failed'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] -top-32 -left-32 pointer-events-none" />
      <div className="absolute w-[400px] h-[400px] bg-emerald-600/10 rounded-full blur-[100px] -bottom-24 -right-24 pointer-events-none" />

      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-indigo-500/25">
            BP
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">BusinessPulse AI</h2>
            <p className="text-xs text-slate-400">Predictive BI & Decision Platform</p>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white">
            {isRegister ? 'Create an enterprise account' : 'Sign in to your organization'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            {isRegister
              ? 'Join to access predictive forecasting and automated decision workflows.'
              : 'Enter your credentials to access the intelligence platform.'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Organization Name</label>
                <div className="relative">
                  <Building className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="Acme Global Inc."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="executive@company.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Password {isRegister && <span className="text-slate-400 font-normal">(min. 6 characters)</span>}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50"
          >
            {isSubmitting ? 'Authenticating...' : isRegister ? 'Complete Registration' : 'Sign In'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-slate-800/80 flex flex-col gap-3">
          <button
            type="button"
            onClick={handleDemoLogin}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 flex items-center justify-center gap-2 transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Quick Demo Login (Acme Corp Admin)
          </button>

          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            className="text-xs text-center text-slate-400 hover:text-indigo-400 transition-colors"
          >
            {isRegister
              ? 'Already have an enterprise account? Sign in'
              : "Don't have an account? Register organization"}
          </button>
        </div>
      </div>
    </div>
  );
};


import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, ArrowRight, Lock, Mail, User, Building, AlertCircle, Sparkles } from 'lucide-react';

const COMMON_DOMAIN_TYPOS: Record<string, string> = {
  'gmaill.com': 'gmail.com',
  'gmai.com': 'gmail.com',
  'gamil.com': 'gmail.com',
  'gmial.com': 'gmail.com',
  'gmaik.com': 'gmail.com',
  'gmaio.com': 'gmail.com',
  'gmaiil.com': 'gmail.com',
  'gmailll.com': 'gmail.com',
  'gemail.com': 'gmail.com',
  'gmail.co': 'gmail.com',
  'gmail.con': 'gmail.com',
  'googlemail.con': 'googlemail.com',
  'yaho.com': 'yahoo.com',
  'yahooo.com': 'yahoo.com',
  'yahoo.con': 'yahoo.com',
  'yaho.co': 'yahoo.com',
  'ymail.con': 'ymail.com',
  'outlok.com': 'outlook.com',
  'outloo.com': 'outlook.com',
  'ootlook.com': 'outlook.com',
  'outlook.con': 'outlook.com',
  'outlock.com': 'outlook.com',
  'hotmial.com': 'hotmail.com',
  'hotmaill.com': 'hotmail.com',
  'hotmali.com': 'hotmail.com',
  'hotmail.con': 'hotmail.com',
  'hotmai.com': 'hotmail.com',
  'iclould.com': 'icloud.com',
  'icoud.com': 'icloud.com',
  'icloud.con': 'icloud.com',
};

const getEmailSuggestion = (emailStr: string): string | null => {
  if (!emailStr || !emailStr.includes('@')) return null;
  const parts = emailStr.split('@');
  if (parts.length !== 2) return null;
  const [username, domain] = parts;
  const lowerDomain = domain.toLowerCase().trim();

  if (COMMON_DOMAIN_TYPOS[lowerDomain]) {
    return `${username}@${COMMON_DOMAIN_TYPOS[lowerDomain]}`;
  }
  if (lowerDomain.endsWith('.con')) {
    return `${username}@${lowerDomain.slice(0, -4)}.com`;
  }
  return null;
};

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

  const emailSuggestion = getEmailSuggestion(email);
  const nameHasNumbers = /\d/.test(name);

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

    // Client-side validations
    if (isRegister) {
      if (nameHasNumbers) {
        setError('Full name cannot contain numbers. Please enter a valid name (e.g. John Doe).');
        return;
      }
      if (name.trim().length < 2) {
        setError('Full name must be at least 2 characters long.');
        return;
      }
      if (!/^[A-Za-zÀ-ÿ\s\.\'-]+$/.test(name.trim())) {
        setError('Full name must contain only letters, spaces, hyphens, and apostrophes.');
        return;
      }
    }

    if (emailSuggestion) {
      setError(`Did you mean ${emailSuggestion}? Please check your email spelling.`);
      return;
    }

    setIsSubmitting(true);

    try {
      if (isRegister) {
        await register(name.trim(), email.trim(), password, orgName.trim());
      } else {
        await login(email.trim(), password);
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
                    className={`w-full bg-slate-950 border rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none ${
                      nameHasNumbers ? 'border-rose-500 focus:border-rose-500' : 'border-slate-800 focus:border-indigo-500'
                    }`}
                  />
                </div>
                {nameHasNumbers && (
                  <p className="mt-1 flex items-center gap-1 text-[11px] text-rose-400">
                    <AlertCircle className="w-3 h-3" />
                    Full name cannot contain numbers (e.g. John Doe).
                  </p>
                )}
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
                className={`w-full bg-slate-950 border rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none ${
                  emailSuggestion ? 'border-amber-500/60 focus:border-amber-500' : 'border-slate-800 focus:border-indigo-500'
                }`}
              />
            </div>
            {emailSuggestion && (
              <div className="mt-1.5 flex items-center justify-between text-[11px] bg-amber-500/10 border border-amber-500/25 px-2.5 py-1.5 rounded-lg text-amber-300">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>
                    Did you mean <strong className="text-white font-medium">{emailSuggestion}</strong>?
                  </span>
                </span>
                <button
                  type="button"
                  onClick={() => setEmail(emailSuggestion)}
                  className="underline hover:text-white font-medium ml-2 shrink-0 cursor-pointer text-amber-200"
                >
                  Use suggestion
                </button>
              </div>
            )}
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


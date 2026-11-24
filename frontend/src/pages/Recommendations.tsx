import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Sparkles,
  RefreshCw,
  Filter,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  Info,
  Brain,
  X
} from 'lucide-react';

interface Recommendation {
  id: string;
  organization_id: string;
  module: string;
  recommendation_type: string;
  title: string;
  description: string;
  affected_entity_type: string;
  affected_entity_id: string;
  evidence: Record<string, any> | null;
  expected_financial_impact: number;
  priority: string;
  status: string;
  created_at: string;
}

interface AIExplanationModalData {
  recommendation_id: string;
  title: string;
  explanation: string;
  grounded_evidence: Record<string, any>;
  generated_by: string;
}

export const Recommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [moduleFilter, setModuleFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  
  // Modals
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);
  const [aiModalData, setAiModalData] = useState<AIExplanationModalData | null>(null);
  const [aiLoading, setAiLoading] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const params: Record<string, string> = {};
      if (moduleFilter !== 'ALL') params.module = moduleFilter;
      if (statusFilter !== 'ALL') params.status = statusFilter;
      
      const res = await api.get('/recommendations', { params });
      setRecommendations(res.data);
    } catch (err: any) {
      console.error('Failed to load recommendations', err);
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = async () => {
    try {
      setGenerating(true);
      setNotification('Evaluating business rules and generating predictive recommendations...');
      const res = await api.post('/recommendations/generate');
      setNotification(`Evaluation finished: ${res.data.total_generated} recommendation(s) generated.`);
      await fetchRecommendations();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: any) {
      setNotification('Failed to run recommendation engine.');
      setTimeout(() => setNotification(null), 5000);
    } finally {
      setGenerating(false);
    }
  };

  const handleExplain = async (rec: Recommendation) => {
    try {
      setAiLoading(true);
      setSelectedRec(rec);
      const res = await api.get(`/recommendations/${rec.id}/explain`);
      setAiModalData(res.data);
    } catch (err: any) {
      console.error('Failed to fetch AI explanation', err);
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [moduleFilter, statusFilter]);

  const filtered = recommendations.filter((r) => {
    if (priorityFilter !== 'ALL' && r.priority !== priorityFilter) return false;
    return true;
  });

  const getPriorityBadge = (p: string) => {
    switch (p.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">Critical Priority</span>;
      case 'HIGH':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">High Priority</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">Medium Priority</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">Low Priority</span>;
    }
  };

  const getStatusBadge = (s: string) => {
    switch (s.toUpperCase()) {
      case 'PENDING':
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">Pending Review</span>;
      case 'APPROVED':
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">Approved</span>;
      case 'EXECUTED':
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">Executed</span>;
      case 'REJECTED':
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">Rejected</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-50 text-slate-700">{s}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Recommendation Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Grounded prescriptive actions generated by ML forecasts, risk thresholds, and deterministic business policies.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={generateRecommendations}
            disabled={generating}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            <Sparkles className={`w-4 h-4 mr-2 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Evaluating Engine...' : 'Run Decision Engine'}
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-900 text-sm flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-indigo-600 font-semibold hover:underline">Dismiss</button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-600 uppercase">Filters:</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500">Module:</span>
          <select
            value={moduleFilter}
            onChange={(e) => setModuleFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-2.5 py-1 text-xs focus:ring-indigo-500"
          >
            <option value="ALL">All Modules</option>
            <option value="SupplyChain">SupplyChain</option>
            <option value="Revenue">Revenue</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500">Priority:</span>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-2.5 py-1 text-xs focus:ring-indigo-500"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-2.5 py-1 text-xs focus:ring-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="EXECUTED">Executed</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>

        <div className="ml-auto text-xs text-slate-500 font-medium">
          Showing {filtered.length} recommendations
        </div>
      </div>

      {/* Recommendation Cards List */}
      {loading ? (
        <div className="h-64 flex items-center justify-center bg-white rounded-xl border border-slate-200">
          <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-500">
          No recommendations found matching current criteria. Click "Run Decision Engine" to trigger evaluation.
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((rec) => (
            <div
              key={rec.id}
              className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-indigo-300 transition space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${
                    rec.module === 'SupplyChain' ? 'bg-blue-50 text-blue-700' : 'bg-emerald-50 text-emerald-700'
                  }`}>
                    {rec.module}
                  </span>
                  {getPriorityBadge(rec.priority)}
                  {getStatusBadge(rec.status)}
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-500 block">Est. Financial Impact</span>
                  <span className="text-base font-bold text-emerald-600">
                    ${rec.expected_financial_impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-900">{rec.title}</h3>
                <p className="text-sm text-slate-600 mt-1 leading-relaxed">{rec.description}</p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
                <div className="flex items-center space-x-4">
                  <span>Target: <strong className="text-slate-700">{rec.affected_entity_type}</strong></span>
                  <span>Type: <strong className="text-slate-700">{rec.recommendation_type}</strong></span>
                  <span>Created: {new Date(rec.created_at).toLocaleDateString()}</span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedRec(rec)}
                    className="inline-flex items-center px-3 py-1.5 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition"
                  >
                    <Info className="w-3.5 h-3.5 mr-1 text-slate-500" />
                    Inspect Evidence
                  </button>
                  <button
                    onClick={() => handleExplain(rec)}
                    className="inline-flex items-center px-3 py-1.5 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-lg hover:bg-indigo-100 transition font-medium"
                  >
                    <Brain className="w-3.5 h-3.5 mr-1 text-indigo-600" />
                    Explain with AI
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Inspect Evidence Modal */}
      {selectedRec && !aiModalData && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">Structured Recommendation Evidence</h3>
              <button onClick={() => setSelectedRec(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div>
              <h4 className="font-semibold text-slate-800">{selectedRec.title}</h4>
              <p className="text-xs text-slate-500 mt-1">{selectedRec.description}</p>
            </div>
            <div className="bg-slate-900 text-slate-100 p-4 rounded-xl text-xs font-mono overflow-x-auto max-h-72">
              <pre>{JSON.stringify(selectedRec.evidence, null, 2)}</pre>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedRec(null)}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Explanation Modal */}
      {aiModalData && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100">
              <div className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-indigo-600" />
                <h3 className="text-lg font-bold text-slate-900">AI Decision Explanation</h3>
              </div>
              <button 
                onClick={() => { setAiModalData(null); setSelectedRec(null); }} 
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Synthesizer Architecture:</span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
                  {aiModalData.generated_by}
                </span>
              </div>
              <h4 className="font-semibold text-slate-900">{aiModalData.title}</h4>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-700 leading-relaxed">
                {aiModalData.explanation}
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Grounded Evidence Factors</h5>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(aiModalData.grounded_evidence).map(([key, val]) => (
                  <div key={key} className="p-2.5 bg-slate-100/70 rounded-lg flex justify-between">
                    <span className="text-slate-600 font-medium">{key.replace(/_/g, ' ')}:</span>
                    <span className="font-bold text-slate-900">{typeof val === 'number' ? val.toLocaleString() : String(val)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => { setAiModalData(null); setSelectedRec(null); }}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
              >
                Understood & Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Recommendations;


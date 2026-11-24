import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  CheckCircle,
  XCircle,
  Play,
  ShieldCheck,
  Clock,
  AlertTriangle,
  RefreshCw,
  FileText,
  Key,
  X
} from 'lucide-react';

interface RecommendationItem {
  id: string;
  module: string;
  recommendation_type: string;
  title: string;
  description: string;
  expected_financial_impact: number;
  priority: string;
  status: string;
  created_at: string;
}

interface ActionItem {
  id: string;
  recommendation_id: string;
  action_type: string;
  execution_status: string;
  idempotency_key: string;
  external_reference: string | null;
  message: string;
  executed_at: string | null;
}

export const Approvals: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pending' | 'actions'>('pending');
  const [pendingList, setPendingList] = useState<RecommendationItem[]>([]);
  const [actionHistory, setActionHistory] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Modals state
  const [selectedRec, setSelectedRec] = useState<RecommendationItem | null>(null);
  const [approvalModalType, setApprovalModalType] = useState<'approve' | 'reject' | null>(null);
  const [commentText, setCommentText] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  
  // Execution
  const [selectedAction, setSelectedAction] = useState<ActionItem | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [pendRes, actRes] = await Promise.all([
        api.get('/approvals/pending'),
        api.get('/actions'),
      ]);
      setPendingList(pendRes.data);
      setActionHistory(actRes.data);
    } catch (err: any) {
      console.error('Failed to load approvals or actions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDecision = async () => {
    if (!selectedRec || !approvalModalType) return;
    try {
      setSubmitting(true);
      if (approvalModalType === 'approve') {
        await api.post(`/approvals/${selectedRec.id}/approve`, {
          comments: commentText || 'Approved via BusinessPulse AI Governance Portal',
        });
        setNotification(`Recommendation "${selectedRec.title}" successfully approved and action queued!`);
      } else {
        if (!commentText.trim()) {
          alert('Please enter a rejection reason.');
          setSubmitting(false);
          return;
        }
        await api.post(`/approvals/${selectedRec.id}/reject`, {
          reason: commentText,
        });
        setNotification(`Recommendation "${selectedRec.title}" has been rejected.`);
      }
      setSelectedRec(null);
      setApprovalModalType(null);
      setCommentText('');
      await fetchData();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: any) {
      alert(`Action failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExecute = async (action: ActionItem) => {
    try {
      setExecuting(true);
      const idempotencyKey = action.idempotency_key || `bp-exec-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const res = await api.post(`/actions/${action.id}/execute`, {
        idempotency_key: idempotencyKey,
      });
      setNotification(`Execution successful: ${res.data.message} (Ref: ${res.data.external_reference || 'ERP-SYNCED'})`);
      await fetchData();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: any) {
      alert(`Execution failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800">Critical</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">High</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">Medium</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800">Low</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Human Approval & Governance</h1>
          <p className="text-sm text-slate-500 mt-1">
            Human-in-the-loop decision control: review, approve, reject, and safely execute AI-generated operational actions with idempotency.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 transition"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {notification && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-emerald-600 font-semibold hover:underline">Dismiss</button>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('pending')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pending'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Pending Review Queue ({pendingList.length})
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'actions'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            Action Execution Log ({actionHistory.length})
          </button>
        </nav>
      </div>

      {/* Tab 1: Pending Approvals */}
      {activeTab === 'pending' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Pending Decision Queue</h2>
              <p className="text-xs text-slate-500">Requires business owner or manager authorization</p>
            </div>
            <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
              {pendingList.length} Awaiting Authorization
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Recommendation</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Module</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Est. Impact</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Governance Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {pendingList.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 text-sm">
                      <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto mb-2 opacity-75" />
                      All recommendations reviewed. Queue is clear!
                    </td>
                  </tr>
                ) : (
                  pendingList.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900">{rec.title}</div>
                        <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{rec.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-medium">
                        {rec.module}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {getPriorityBadge(rec.priority)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-bold text-emerald-600 text-sm">
                        ${rec.expected_financial_impact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                        {new Date(rec.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="inline-flex items-center space-x-2">
                          <button
                            onClick={() => { setSelectedRec(rec); setApprovalModalType('approve'); }}
                            className="inline-flex items-center px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition shadow-sm"
                          >
                            <CheckCircle className="w-3.5 h-3.5 mr-1" />
                            Approve
                          </button>
                          <button
                            onClick={() => { setSelectedRec(rec); setApprovalModalType('reject'); }}
                            className="inline-flex items-center px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-medium transition"
                          >
                            <XCircle className="w-3.5 h-3.5 mr-1" />
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Action Executions */}
      {activeTab === 'actions' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">Executed & Pending ERP/CRM Actions</h2>
            <span className="text-xs text-slate-500">{actionHistory.length} total recorded</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Action Type</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">External Ref</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Execution Message</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Executed At</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Execute</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {actionHistory.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-500 text-sm">
                      No actions recorded yet. Approved recommendations will spawn executable actions here.
                    </td>
                  </tr>
                ) : (
                  actionHistory.map((act) => (
                    <tr key={act.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-900 text-sm">
                        {act.action_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          act.execution_status === 'SUCCESS'
                            ? 'bg-emerald-100 text-emerald-800'
                            : act.execution_status === 'FAILED'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {act.execution_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-slate-600">
                        {act.external_reference || '—'}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-600 max-w-xs truncate">
                        {act.message}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                        {act.executed_at ? new Date(act.executed_at).toLocaleString() : 'Not executed'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {act.execution_status === 'PENDING' ? (
                          <button
                            onClick={() => handleExecute(act)}
                            disabled={executing}
                            className="inline-flex items-center px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium transition shadow-sm disabled:opacity-50"
                          >
                            <Play className="w-3 h-3 mr-1" />
                            Execute
                          </button>
                        ) : (
                          <span className="text-xs text-emerald-600 font-semibold flex items-center justify-center">
                            <CheckCircle className="w-3.5 h-3.5 mr-1" /> Synchronized
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Decision Modal (Approve / Reject) */}
      {selectedRec && approvalModalType && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">
                {approvalModalType === 'approve' ? 'Approve Recommendation' : 'Reject Recommendation'}
              </h3>
              <button 
                onClick={() => { setSelectedRec(null); setApprovalModalType(null); }}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              <h4 className="font-semibold text-slate-800 text-sm">{selectedRec.title}</h4>
              <p className="text-xs text-slate-500">{selectedRec.description}</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                {approvalModalType === 'approve' ? 'Approval Notes (Optional):' : 'Rejection Reason (Required):'}
              </label>
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder={approvalModalType === 'approve' ? 'Authorized for ERP dispatch...' : 'State business reason for rejection...'}
                className="w-full border border-slate-300 rounded-lg p-2.5 text-xs focus:ring-2 focus:ring-indigo-500 h-24"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => { setSelectedRec(null); setApprovalModalType(null); }}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium hover:bg-slate-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDecision}
                disabled={submitting}
                className={`px-4 py-2 rounded-lg text-xs font-medium text-white shadow-sm transition disabled:opacity-50 ${
                  approvalModalType === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'
                }`}
              >
                {submitting ? 'Submitting...' : approvalModalType === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Approvals;


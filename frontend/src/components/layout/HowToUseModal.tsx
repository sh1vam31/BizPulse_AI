import React from 'react';
import { Link } from 'react-router-dom';
import {
  X,
  UploadCloud,
  Brain,
  CheckSquare,
  Sliders,
  ArrowRight,
  BookOpen,
} from 'lucide-react';

interface HowToUseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HowToUseModal: React.FC<HowToUseModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-3xl w-full shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-indigo-600 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <BookOpen className="w-5 h-5" />
            <div>
              <h2 className="text-base font-bold">How to Use BusinessPulse AI (Step-by-Step)</h2>
              <p className="text-xs text-indigo-100">Follow these 4 simple steps to turn your raw data into live forecasts and business actions.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-indigo-500 transition-colors text-white"
            aria-label="Close guide"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Steps Body */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">1</span>
                  <UploadCloud className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-sm font-bold text-slate-900">Upload &amp; Validate Data</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Open <strong>Data Sources &amp; Ingest</strong>, pick your schema (e.g. <em>Sales Transactions</em>), choose your CSV/Excel file, click <strong>Dry-Run Validation Preview</strong> to check for errors, then click <strong>Confirm &amp; Commit Ingestion</strong>.
                </p>
              </div>
              <Link
                to="/data-sources"
                onClick={onClose}
                className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline"
              >
                Open Data Sources <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">2</span>
                  <Brain className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-sm font-bold text-slate-900">Run AI &amp; ML Forecasts</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Visit <strong>SupplyChain Intelligence</strong> and <strong>Revenue Intelligence</strong>, then click <strong>Re-run ML Forecaster / Pipeline</strong> to generate demand predictions, stockout alerts, churn risk, and customer segments.
                </p>
              </div>
              <div className="mt-3 flex items-center gap-4">
                <Link to="/supply-chain" onClick={onClose} className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  SupplyChain <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link to="/revenue" onClick={onClose} className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  Revenue <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">3</span>
                  <CheckSquare className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-sm font-bold text-slate-900">Generate &amp; Approve Actions</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Go to <strong>Recommendations</strong> and click <strong>Run Decision Engine</strong>. Then open <strong>Approval Center</strong> to <strong>Approve</strong> or <strong>Reject</strong> AI suggestions and dispatch actions.
                </p>
              </div>
              <div className="mt-3 flex items-center gap-4">
                <Link to="/recommendations" onClick={onClose} className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  Recommendations <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link to="/approvals" onClick={onClose} className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline">
                  Approval Center <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">4</span>
                  <Sliders className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-sm font-bold text-slate-900">Stress-Test What-If Scenarios</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Use <strong>What-If Simulations</strong> to adjust demand surges, supplier delays, or price changes with sliders and see projected financial impact before making real decisions.
                </p>
              </div>
              <Link
                to="/simulations"
                onClick={onClose}
                className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline"
              >
                Open Simulations <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm"
          >
            Got It, Let&apos;s Start
          </button>
        </div>
      </div>
    </div>
  );
};


import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Database,
  Check,
  X,
  FileText
} from 'lucide-react';

interface DataSource {
  id: string;
  source_name: string;
  source_type: string;
  status: string;
  created_at: string;
}

interface ImportJob {
  id: string;
  source_id: string;
  file_name: string;
  records_processed: number;
  records_failed: number;
  status: string;
  error_summary: string | null;
  created_at: string;
}

interface ValidationReport {
  is_valid: boolean;
  detected_entity_type: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  column_mappings: Record<string, string>;
  errors: Array<{ row?: number; column?: string; message?: string; error?: string; raw?: any }>;
  sample_preview: any[];
}

export const DataSources: React.FC = () => {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Upload & Validation state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [entityType, setEntityType] = useState<string>('sales');
  const [validating, setValidating] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [srcRes, jobRes] = await Promise.all([
        api.get('/data/sources'),
        api.get('/data/imports'),
      ]);
      setSources(srcRes.data);
      setJobs(jobRes.data);
    } catch (err: any) {
      console.error('Failed to load data sources', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setValidationReport(null);
      setErrorMessage(null);
    }
  };

  const handleValidate = async () => {
    if (!selectedFile) return;
    try {
      setValidating(true);
      setErrorMessage(null);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('entity_type', entityType);

      const res = await api.post('/data/validate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setValidationReport(res.data);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Validation failed';
      setErrorMessage(`Validation failed: ${msg}`);
    } finally {
      setValidating(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      setUploading(true);
      setErrorMessage(null);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('entity_type', entityType);

      const res = await api.post('/data/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const processed = res.data.records_processed?.toLocaleString() || '0';
      const failed = res.data.records_failed?.toLocaleString() || '0';
      setNotification(`Data successfully imported! Processed: ${processed} records (${failed} skipped/invalid).`);
      setSelectedFile(null);
      setValidationReport(null);
      await fetchData();
      setTimeout(() => setNotification(null), 10000);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Ingestion failed';
      setErrorMessage(`Upload failed: ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Data Integration & Ingestion Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Connect CSV & Excel feeds from ERP, CRM, and inventory databases with dry-run schema validation and error reporting.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 transition"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {notification && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-emerald-600 font-semibold hover:underline">Dismiss</button>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-900 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-600 font-semibold hover:underline ml-4">Dismiss</button>
        </div>
      )}

      {/* Upload & Validation Studio */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 className="text-base font-bold text-slate-900 flex items-center">
            <UploadCloud className="w-5 h-5 mr-2 text-indigo-600" />
            Ingest Dataset (CSV or Excel)
          </h2>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className={`px-2.5 py-1 rounded-full font-semibold ${!selectedFile ? 'bg-indigo-600 text-white' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}`}>
              1. Choose File
            </span>
            <span className="text-slate-400">→</span>
            <span className={`px-2.5 py-1 rounded-full font-semibold ${selectedFile && !validationReport ? 'bg-indigo-600 text-white' : validationReport ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'}`}>
              2. Dry-Run Check
            </span>
            <span className="text-slate-400">→</span>
            <span className={`px-2.5 py-1 rounded-full font-semibold ${validationReport ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
              3. Confirm &amp; Commit
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Target Entity Schema:
            </label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
            >
              <option value="sales">Sales Transactions</option>
              <option value="inventory">Inventory Levels</option>
              <option value="customers">Customer Directory</option>
              <option value="suppliers">Suppliers</option>
              <option value="orders">Purchase Orders</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Select Data File (.csv, .xlsx, .xls):
            </label>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
          </div>
        </div>

        {selectedFile && (
          <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3 pt-2">
            <button
              onClick={handleValidate}
              disabled={validating || uploading}
              className="px-4 py-2 bg-slate-800 text-white rounded-lg text-xs font-semibold hover:bg-slate-900 transition disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {validating && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{validating ? 'Validating Dataset in Memory...' : 'Dry-Run Validation Preview'}</span>
            </button>
            <button
              onClick={handleUpload}
              disabled={uploading || validating}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 transition disabled:opacity-50 shadow-sm flex items-center justify-center space-x-2"
            >
              {uploading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{uploading ? 'Ingesting & Batch Indexing...' : 'Confirm & Commit Ingestion'}</span>
            </button>
          </div>
        )}

        {/* Validation Report Card */}
        {validationReport && (
          <div className="mt-4 p-5 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {validationReport.is_valid ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-amber-600" />
                )}
                <h3 className="font-bold text-slate-900 text-sm">
                  Dry-Run Validation: {validationReport.is_valid ? 'Schema Valid' : 'Schema Warnings / Issues Found'}
                </h3>
              </div>
              <div className="flex space-x-3 text-xs">
                <span className="font-semibold text-slate-600">Total: {validationReport.total_rows}</span>
                <span className="font-semibold text-emerald-600">Valid: {validationReport.valid_rows}</span>
                <span className="font-semibold text-rose-600">Invalid: {validationReport.invalid_rows}</span>
              </div>
            </div>

            {/* Column Mappings */}
            <div>
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                Auto-Detected Column Mappings:
              </span>
              <div className="flex flex-wrap gap-2">
                {Object.entries(validationReport.column_mappings).map(([rawCol, targetCol]) => (
                  <span key={rawCol} className="px-2.5 py-1 bg-white border border-slate-200 rounded text-xs text-slate-700">
                    <span className="text-slate-400">{rawCol}</span> → <strong className="text-indigo-600">{targetCol}</strong>
                  </span>
                ))}
              </div>
            </div>

            {/* Errors if any */}
            {validationReport.errors && validationReport.errors.length > 0 && (
              <div className="space-y-1">
                <span className="text-xs font-semibold text-rose-700 block">Row Validation Errors:</span>
                <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-800 space-y-1 max-h-36 overflow-y-auto">
                  {validationReport.errors.map((err, i) => (
                    <div key={i}>
                      {err.row ? `Row ${err.row}${err.column ? ` (${err.column})` : ''}: ` : ''}
                      {err.message || err.error || 'Invalid value'}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Ingestion Jobs History Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Ingestion Audit Log & Job History</h2>
          <span className="text-xs text-slate-500">{jobs.length} jobs recorded</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">File Name</th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Processed</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Failed</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Error Details</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Timestamp</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-500 text-sm">
                    No ingestion jobs recorded yet.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-900 text-sm">
                      {job.file_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        job.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                      }`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-emerald-600">
                      {job.records_processed}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold text-rose-600">
                      {job.records_failed}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-600 max-w-xs truncate">
                      {job.error_summary || 'None'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DataSources;


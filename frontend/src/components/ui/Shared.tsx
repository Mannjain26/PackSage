import React from 'react';

interface StatusBadgeProps { status: string; }
export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const map: Record<string, string> = {
    completed: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    in_progress: 'bg-amber-50 text-amber-700 border border-amber-200',
    draft: 'bg-gray-100 text-gray-600 border border-gray-300',
    verified: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    pending: 'bg-amber-50 text-amber-700 border border-amber-200',
    failed: 'bg-red-50 text-red-600 border border-red-200',
    admin: 'bg-purple-50 text-purple-700 border border-purple-200',
    engineer: 'bg-blue-50 text-blue-700 border border-blue-200',
    field_user: 'bg-gray-100 text-gray-600 border border-gray-300',
  };
  const key = status.toLowerCase().replace(' ', '_');
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[key] || 'bg-gray-100 text-gray-600 border border-gray-300'}`}>
      {status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
    </span>
  );
};

interface KpiCardProps { title: string; value: string | number; sub?: string; onClick?: () => void; }
export const KpiCard: React.FC<KpiCardProps> = ({ title, value, sub, onClick }) => (
  <div
    className={`bg-white border border-gray-200 rounded-xl p-5 shadow-sm ${onClick ? 'cursor-pointer hover:border-emerald-400 hover:shadow-md transition-all' : ''}`}
    onClick={onClick}
  >
    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">{title}</p>
    <p className="text-3xl font-bold text-gray-800">{value}</p>
    {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
  </div>
);

interface LoadingSkeletonProps { rows?: number; }
export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ rows = 5 }) => (
  <div className="space-y-3 animate-pulse">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-10 bg-gray-100 rounded-lg" />
    ))}
  </div>
);

interface ErrorBoxProps { message: string; }
export const ErrorBox: React.FC<ErrorBoxProps> = ({ message }) => (
  <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
    ⚠ {message}
  </div>
);

export const DisclaimerBanner: React.FC = () => (
  <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 flex items-start gap-2">
    <span className="mt-0.5 flex-shrink-0">⚠</span>
    <span><strong>Decision-support only</strong> — requires engineer review and sign-off before implementation. Not a substitute for laboratory testing or regulatory compliance review.</span>
  </div>
);

interface EmptyStateProps { message: string; action?: React.ReactNode; }
export const EmptyState: React.FC<EmptyStateProps> = ({ message, action }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
      <span className="text-2xl">📦</span>
    </div>
    <p className="text-gray-500 text-sm mb-4">{message}</p>
    {action}
  </div>
);

export const EvidenceBadge: React.FC<{ type: 'Verified' | 'Estimated' | 'Illustrative' | 'Default' | string }> = ({ type }) => {
  const map: Record<string, string> = {
    Verified: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    Estimated: 'bg-amber-100 text-amber-800 border-amber-300',
    Illustrative: 'bg-purple-100 text-purple-800 border-purple-300',
    Default: 'bg-gray-100 text-gray-700 border-gray-300',
  };
  const style = map[type] || 'bg-blue-100 text-blue-800 border-blue-300';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${style}`}>
      ● {type}
    </span>
  );
};


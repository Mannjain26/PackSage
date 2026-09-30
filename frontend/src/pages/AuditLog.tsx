import React from 'react';
import { useQuery } from '@tanstack/react-query';
import Layout from '../components/layout/Layout';
import { getAuditLog } from '../services/dashboardApi';
import { LoadingSkeleton, StatusBadge } from '../components/ui/Shared';

const AuditLog: React.FC = () => {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit'],
    queryFn: getAuditLog,
  });

  return (
    <Layout title="System Audit Log">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-6"><LoadingSkeleton rows={15} /></div>
        ) : (
          <div className="overflow-x-auto h-[calc(100vh-140px)]">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-white shadow-sm z-10">
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-200">
                  <th className="px-6 py-3 font-medium">Timestamp</th>
                  <th className="px-6 py-3 font-medium">Action</th>
                  <th className="px-6 py-3 font-medium">Entity Type</th>
                  <th className="px-6 py-3 font-medium">Entity ID</th>
                  <th className="px-6 py-3 font-medium">User ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {logs?.map((l: any) => (
                  <tr key={l.id} className="hover:bg-gray-50 font-mono text-xs text-gray-600">
                    <td className="px-6 py-3">{new Date(l.timestamp).toISOString()}</td>
                    <td className="px-6 py-3 font-bold text-gray-800"><StatusBadge status={l.action} /></td>
                    <td className="px-6 py-3">{l.entity_type || '-'}</td>
                    <td className="px-6 py-3 truncate max-w-[150px]" title={l.entity_id}>{l.entity_id || '-'}</td>
                    <td className="px-6 py-3 truncate max-w-[150px]" title={l.user_id}>{l.user_id || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AuditLog;

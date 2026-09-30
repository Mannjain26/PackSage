import React from 'react';
import { useQuery } from '@tanstack/react-query';
import Layout from '../components/layout/Layout';
import api, { downloadReportFile } from '../services/api';
import { LoadingSkeleton, EmptyState } from '../components/ui/Shared';
import { FileDown, QrCode } from 'lucide-react';

const Reports: React.FC = () => {
  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const { data } = await api.get('/reports');
      return data;
    },
  });

  const downloadReport = async (id: string, uuid: string) => {
    try {
      await downloadReportFile(id, `PackSage_Report_${uuid.slice(0, 8)}.pdf`);
    } catch (err) {
      console.error("Failed to download report", err);
    }
  };

  return (
    <Layout title="Generated Reports">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-6"><LoadingSkeleton /></div>
        ) : reports?.length === 0 ? (
          <EmptyState message="No reports generated yet. Run a scenario to generate a report." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-200">
                  <th className="px-6 py-3 font-medium">Report UUID</th>
                  <th className="px-6 py-3 font-medium">Scenario</th>
                  <th className="px-6 py-3 font-medium">Date Generated</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {reports?.map((r: any) => (
                  <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-gray-600 flex items-center gap-2">
                      <QrCode size={14} className="text-gray-400" /> {r.qr_code_value}
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900">{r.scenario_name}</td>
                    <td className="px-6 py-4 text-gray-500">{new Date(r.generated_at).toLocaleString()}</td>
                    <td className="px-6 py-4 text-right">
                      {r.has_file ? (
                        <button 
                          onClick={() => downloadReport(r.id, r.qr_code_value)}
                          className="flex items-center justify-end gap-1 text-emerald-600 hover:text-emerald-700 font-medium ml-auto"
                        >
                          <FileDown size={16} /> Download
                        </button>
                      ) : (
                        <span className="text-gray-400 text-xs">File unavailable</span>
                      )}
                    </td>
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

export default Reports;

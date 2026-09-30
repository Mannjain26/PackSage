import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import { getDashboardStats, getRecentScenarios } from '../services/dashboardApi';
import { KpiCard, StatusBadge, LoadingSkeleton } from '../components/ui/Shared';
import { useAuth } from '../context/AuthContext';
import { Plus } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: getDashboardStats,
  });

  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ['recentScenarios'],
    queryFn: getRecentScenarios,
  });

  return (
    <Layout
      title="Packaging Intelligence Dashboard"
      actions={
        <button
          onClick={() => navigate('/scenarios/new')}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Scenario
        </button>
      }
    >
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Welcome back, {user?.name?.split(' ')[0]}</h2>
          <p className="text-gray-500 mt-1">Here is the latest packaging intelligence data.</p>
        </div>
      </div>

      {statsLoading ? (
        <LoadingSkeleton rows={1} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KpiCard title="Active Scenarios" value={stats?.active_scenarios || 0} onClick={() => navigate('/scenarios')} />
          <KpiCard title="Materials in KB" value={stats?.materials_in_kb || 0} onClick={() => navigate('/materials')} />
          <KpiCard title="Reports Generated" value={stats?.reports_generated || 0} onClick={() => navigate('/reports')} />
          <KpiCard title="Pending Review" value={stats?.pending_material_verification || 0} onClick={user?.role !== 'field_user' ? () => navigate('/materials?tab=pending') : undefined} />
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Recent Scenarios</h3>
          <button onClick={() => navigate('/scenarios')} className="text-sm font-medium text-emerald-600 hover:text-emerald-700">View All</button>
        </div>
        
        {recentLoading ? (
          <div className="p-6"><LoadingSkeleton /></div>
        ) : recent?.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No scenarios found. Create one to get started.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-200">
                  <th className="px-6 py-3 font-medium">Commodity</th>
                  <th className="px-6 py-3 font-medium">Storage</th>
                  <th className="px-6 py-3 font-medium">Shelf Life Target</th>
                  <th className="px-6 py-3 font-medium">Date</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {recent?.map((s: any) => (
                  <tr key={s.id} onClick={() => navigate(`/scenario/${s.id}/results`)} className="hover:bg-gray-50 cursor-pointer transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{s.commodity_name}</td>
                    <td className="px-6 py-4 text-gray-600 capitalize">{s.storage_type}</td>
                    <td className="px-6 py-4 text-gray-600">{s.target_shelf_life_days} days</td>
                    <td className="px-6 py-4 text-gray-500">{new Date(s.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4"><StatusBadge status={s.status} /></td>
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

export default Dashboard;

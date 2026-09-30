import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import { getScenarios, deleteScenario } from '../services/scenarioApi';
import { StatusBadge, LoadingSkeleton, EmptyState } from '../components/ui/Shared';
import { Plus, Trash2 } from 'lucide-react';

const Scenarios: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: scenarios, isLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => getScenarios(),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteScenario(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scenarios'] }),
  });

  return (
    <Layout
      title="All Scenarios"
      actions={
        <button
          onClick={() => navigate('/scenarios/new')}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Scenario
        </button>
      }
    >
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-6"><LoadingSkeleton /></div>
        ) : scenarios?.length === 0 ? (
          <EmptyState
            message="No scenarios found. Create one to get started."
            action={
              <button onClick={() => navigate('/scenarios/new')} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
                Create Scenario
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-200">
                  <th className="px-6 py-3 font-medium">Commodity</th>
                  <th className="px-6 py-3 font-medium">Category</th>
                  <th className="px-6 py-3 font-medium">Storage</th>
                  <th className="px-6 py-3 font-medium">Shelf Life Target</th>
                  <th className="px-6 py-3 font-medium">Created Date</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {scenarios?.map((s: any) => (
                  <tr key={s.id} onClick={() => navigate(`/scenario/${s.id}/results`)} className="hover:bg-gray-50 cursor-pointer transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{s.commodity_name}</td>
                    <td className="px-6 py-4 text-gray-600 capitalize">{s.commodity_category.replace('_', ' ')}</td>
                    <td className="px-6 py-4 text-gray-600 capitalize">{s.storage_type}</td>
                    <td className="px-6 py-4 text-gray-600">{s.target_shelf_life_days} days</td>
                    <td className="px-6 py-4 text-gray-500">{new Date(s.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4"><StatusBadge status={s.status} /></td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Are you sure you want to delete scenario "${s.commodity_name}"?`)) {
                            deleteMut.mutate(s.id);
                          }
                        }}
                        className="text-red-500 hover:text-red-700 p-1.5 rounded hover:bg-red-50 transition-colors"
                        title="Delete Scenario"
                      >
                        <Trash2 size={16} />
                      </button>
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

export default Scenarios;

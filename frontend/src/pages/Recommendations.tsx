import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import { getScenarios } from '../services/scenarioApi';
import { LoadingSkeleton, EmptyState, StatusBadge } from '../components/ui/Shared';
import { Plus, ArrowRight, Clock } from 'lucide-react';

const Recommendations: React.FC = () => {
  const navigate = useNavigate();
  const { data: scenarios, isLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => getScenarios(),
  });

  return (
    <Layout
      title="Saved Recommendations & History"
      actions={
        <button
          onClick={() => navigate('/scenarios/new')}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Recommendation
        </button>
      }
    >
      <div className="space-y-6">
        <p className="text-sm text-gray-600">
          Select any of your packaging evaluation scenarios below to view or re-calculate candidate material rankings, ML fit scores, and export compliance reports.
        </p>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <LoadingSkeleton rows={5} />
            <LoadingSkeleton rows={5} />
            <LoadingSkeleton rows={5} />
          </div>
        ) : !scenarios || scenarios.length === 0 ? (
          <EmptyState
            message="No recommendation scenarios found yet. Run an analysis to generate packaging recommendations."
            action={
              <button
                onClick={() => navigate('/scenarios/new')}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Create First Scenario
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scenarios.map((s: any) => (
              <div
                key={s.id}
                onClick={() => navigate(`/scenario/${s.id}/results`)}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-emerald-300 transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        {s.commodity_category.replace('_', ' ')}
                      </span>
                      <h3 className="text-lg font-bold text-gray-900 mt-1">{s.commodity_name}</h3>
                    </div>
                    <StatusBadge status={s.status} />
                  </div>

                  <div className="space-y-2 text-xs text-gray-600 border-t border-gray-100 pt-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Storage:</span>
                      <span className="font-medium capitalize">{s.storage_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target Shelf Life:</span>
                      <span className="font-medium">{s.target_shelf_life_days} days</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-400">
                      <span className="flex items-center gap-1"><Clock size={12} /> Created:</span>
                      <span>{new Date(s.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-emerald-600 font-semibold">
                  <span>View Material Results</span>
                  <ArrowRight size={14} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Recommendations;

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Layout from '../components/layout/Layout';
import { getMaterials, verifyMaterial } from '../services/materialApi';
import { useAuth } from '../context/AuthContext';
import { StatusBadge, LoadingSkeleton } from '../components/ui/Shared';
import { Search, Filter, ShieldCheck } from 'lucide-react';

const Materials: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');

  const { data: materials, isLoading } = useQuery({
    queryKey: ['materials', search, filterType],
    queryFn: () => getMaterials({ search: search || undefined, mat_type: filterType || undefined }),
  });

  const verifyMut = useMutation({
    mutationFn: (id: string) => verifyMaterial(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materials'] }),
  });

  const canVerify = user?.role === 'admin' || user?.role === 'engineer';

  return (
    <Layout title="Materials Knowledge Base">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[calc(100vh-140px)]">
        
        {/* Toolbar */}
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Search materials..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm"
            />
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="text-gray-400" size={18} />
            <select 
              value={filterType} 
              onChange={e => setFilterType(e.target.value)}
              className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm bg-white"
            >
              <option value="">All Types</option>
              <option value="LDPE">LDPE</option>
              <option value="HDPE">HDPE</option>
              <option value="PET">PET</option>
              <option value="BOPP">BOPP</option>
              <option value="metalized">Metalized</option>
              <option value="foil_laminate">Foil Laminate</option>
              <option value="biodegradable">Biodegradable</option>
              <option value="breathable">Breathable (MAP)</option>
              <option value="high_barrier">High Barrier</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto">
          {isLoading ? (
            <div className="p-6"><LoadingSkeleton rows={10} /></div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-white z-10 shadow-sm">
                <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-200">
                  <th className="px-6 py-3 font-medium">Material Name</th>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Commercial Price</th>
                  <th className="px-6 py-3 font-medium">Density</th>
                  <th className="px-6 py-3 font-medium">Barrier (OTR / WVTR)</th>
                  <th className="px-6 py-3 font-medium text-center">Food Safe</th>
                  <th className="px-6 py-3 font-medium text-center">Recyclable</th>
                  <th className="px-6 py-3 font-medium text-center">Status</th>
                  {canVerify && <th className="px-6 py-3 font-medium text-right">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {materials?.map((m: any) => {
                  const curr = m.currency === 'USD' ? '$' : (m.currency === 'EUR' ? '€' : '₹');
                  return (
                    <tr key={m.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 font-medium text-gray-900">{m.name}</td>
                      <td className="px-6 py-3 text-gray-600 capitalize">{m.mat_type.replace('_', ' ')}</td>
                      <td className="px-6 py-3">
                        <div className="font-semibold text-emerald-700">
                          {m.price_per_kg ? `${curr}${m.price_per_kg}/kg` : 'N/A'}
                        </div>
                        <div className="text-[10px] text-gray-400">
                          {m.price_confidence || 'indicative'} ({m.price_source || 'market benchmark'})
                        </div>
                      </td>
                      <td className="px-6 py-3 text-gray-700 text-xs font-mono">
                        {m.material_density_g_cm3 ? `${m.material_density_g_cm3} g/cm³` : 'N/A'}
                      </td>
                      <td className="px-6 py-3 text-gray-500 text-xs">
                        {m.otr || 'N/A'} cc / {m.wvtr || 'N/A'} g
                      </td>
                      <td className="px-6 py-3 text-center">{m.food_contact_safe ? '✅' : '❌'}</td>
                      <td className="px-6 py-3 text-center">{m.recyclable ? '✅' : '❌'}</td>
                      <td className="px-6 py-3 text-center">
                        <StatusBadge status={m.verified ? 'verified' : 'pending'} />
                      </td>
                      {canVerify && (
                        <td className="px-6 py-3 text-right">
                          {!m.verified && (
                            <button 
                              onClick={() => verifyMut.mutate(m.id)}
                              disabled={verifyMut.isPending}
                              className="flex items-center justify-end gap-1 text-emerald-600 hover:text-emerald-700 font-medium disabled:opacity-50 ml-auto"
                            >
                              <ShieldCheck size={16} /> Verify
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Materials;

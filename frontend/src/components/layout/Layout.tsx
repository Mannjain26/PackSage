import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard, FlaskConical, Star, BookOpen, FileText, ShieldCheck, LogOut, User, Menu, Sparkles
} from 'lucide-react';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/inverse-solver', label: 'Shelf-Life Solver', icon: Sparkles },
  { to: '/scenarios', label: 'Scenarios', icon: FlaskConical },
  { to: '/recommendations', label: 'Recommendations', icon: Star },
  { to: '/materials', label: 'Materials Library', icon: BookOpen },
  { to: '/reports', label: 'Reports', icon: FileText },
];
const ADMIN_NAV = [
  { to: '/admin/audit', label: 'Audit Log', icon: ShieldCheck },
];

interface LayoutProps { children: React.ReactNode; title?: string; actions?: React.ReactNode; }

const Layout: React.FC<LayoutProps> = ({ children, title, actions }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const allNav = user?.role !== 'field_user' ? [...NAV, ...ADMIN_NAV] : NAV;

  const handleLogout = () => { logout(); navigate('/login'); };

  const Sidebar = () => (
    <nav className="flex flex-col h-full">
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <div>
            <p className="text-sm font-bold text-gray-800 leading-tight">PackSage AI</p>
            <p className="text-[10px] text-gray-400 leading-tight">SIH260236</p>
          </div>
        </div>
      </div>
      <div className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
        {allNav.map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.to || location.pathname.startsWith(item.to + '/');
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </div>
      <div className="px-3 py-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
            <User size={14} className="text-emerald-700" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-800 truncate">{user?.name}</p>
            <p className="text-[10px] text-gray-400 truncate">{user?.role?.replace('_', ' ')}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-xs text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg w-full transition-all"
        >
          <LogOut size={14} /> Sign out
        </button>
      </div>
    </nav>
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-60 bg-white border-r border-gray-200 shadow-sm flex-shrink-0">
        <Sidebar />
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div className="fixed inset-0 bg-black/30" onClick={() => setMobileOpen(false)} />
          <div className="relative w-60 bg-white shadow-xl z-50">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between flex-shrink-0 shadow-sm">
          <div className="flex items-center gap-4">
            <button onClick={() => setMobileOpen(true)} className="lg:hidden text-gray-500 hover:text-gray-700">
              <Menu size={20} />
            </button>
            {title && <h1 className="text-base font-semibold text-gray-800">{title}</h1>}
          </div>
          <div className="flex items-center gap-3">{actions}</div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default Layout;

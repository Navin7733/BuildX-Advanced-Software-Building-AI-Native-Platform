import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, Activity, Database, LogOut } from 'lucide-react';
import useStore from '../../store/useStore';

const Shell = () => {
  const { user, logout, activeProject } = useStore();
  const location = useLocation();

  const handleLogout = () => {
    logout();
  };

  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/' },
    ...(activeProject ? [
      { name: 'Project Overview', icon: FolderKanban, path: `/project/${activeProject.id}` },
      { name: 'Agent Workspace', icon: Activity, path: `/project/${activeProject.id}/workspace` },
      { name: 'Memory & Decisions', icon: Database, path: `/project/${activeProject.id}/memory` },
    ] : [])
  ];

  return (
    <div className="flex h-screen w-full bg-slate-900 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 glass-panel border-r border-slate-700/50 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-700/50">
          <div className="flex items-center gap-2 text-violet-500 font-bold text-xl tracking-wider">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-violet-600 to-blue-600 flex items-center justify-center text-white">
              B
            </div>
            BuildX
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <item.icon size={18} />
                <span className="font-medium text-sm">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-700/50">
          <div className="flex items-center justify-between px-3 py-2">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <div className="truncate text-sm">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-xs text-slate-500 truncate">{user?.email}</p>
              </div>
            </div>
            <button 
              onClick={handleLogout}
              className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-900 to-slate-950">
        <header className="h-16 flex items-center justify-between px-8 border-b border-slate-800/50 glass z-10 flex-shrink-0">
          <h1 className="text-lg font-semibold text-slate-200">
            {activeProject ? activeProject.name : 'Dashboard'}
          </h1>
          <div className="flex items-center gap-4">
             {/* Header actions (e.g. settings, notifications) can go here */}
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8 relative">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Shell;

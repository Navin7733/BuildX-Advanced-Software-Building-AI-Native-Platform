import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, TerminalSquare, BrainCircuit,
  ChevronLeft, LogOut, Menu, Zap, FolderKanban,
  ChevronRight
} from 'lucide-react';
import useStore from '../../store/useStore';

const Shell = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const { user, activeProject, logout } = useStore();

  // Detect project context from URL
  const projectMatch = location.pathname.match(/\/project\/([^/]+)/);
  const currentProjectId = projectMatch ? projectMatch[1] : null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const globalNav = [
    { label: 'Dashboard', icon: LayoutDashboard, to: '/', exact: true },
  ];

  const projectNav = currentProjectId
    ? [
        { label: 'Overview', icon: FolderKanban, to: `/project/${currentProjectId}`, exact: true },
        { label: 'Agent Workspace', icon: TerminalSquare, to: `/project/${currentProjectId}/workspace` },
        { label: 'Memory & Decisions', icon: BrainCircuit, to: `/project/${currentProjectId}/memory` },
      ]
    : [];

  const isActive = (item) =>
    item.exact ? location.pathname === item.to : location.pathname.startsWith(item.to);

  // Breadcrumb segments
  const breadcrumbs = (() => {
    const crumbs = [{ label: 'Dashboard', to: '/' }];
    if (activeProject && currentProjectId) {
      crumbs.push({ label: activeProject.name, to: `/project/${currentProjectId}` });
      if (location.pathname.includes('/workspace')) crumbs.push({ label: 'Workspace', to: null });
      else if (location.pathname.includes('/memory')) crumbs.push({ label: 'Memory', to: null });
    }
    return crumbs;
  })();

  return (
    <div className="flex h-screen w-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      {/* ─── Sidebar ─── */}
      <aside
        className={`flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out z-20
          ${sidebarOpen ? 'w-64' : 'w-[60px]'}`}
        style={{
          background: 'var(--surface-0)',
          borderRight: '1px solid var(--border-subtle)',
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center h-16 px-4 shrink-0"
          style={{ borderBottom: '1px solid var(--border-subtle)' }}
        >
          <div className={`flex items-center gap-3 w-full ${!sidebarOpen && 'justify-center'}`}>
            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'linear-gradient(135deg, var(--accent-violet), var(--accent-blue))', boxShadow: '0 0 20px rgba(139,92,246,0.25)' }}>
              <Zap size={16} className="text-white" strokeWidth={2.5} />
            </div>
            {sidebarOpen && (
              <span className="font-bold text-lg text-white tracking-tight flex-1">BuildX</span>
            )}
            {sidebarOpen && (
              <button onClick={() => setSidebarOpen(false)} className="text-slate-600 hover:text-white transition-colors p-1 rounded">
                <ChevronLeft size={18} />
              </button>
            )}
          </div>
          {!sidebarOpen && (
            <button onClick={() => setSidebarOpen(true)} className="absolute left-0 w-[60px] flex justify-center text-slate-600 hover:text-white transition-colors p-1 rounded">
            </button>
          )}
        </div>

        {/* Expand toggle when collapsed */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="mx-auto mt-2 p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-colors"
          >
            <Menu size={16} />
          </button>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 space-y-0.5 px-2">
          {globalNav.map((item) => (
            <NavItem key={item.to} item={item} active={isActive(item)} collapsed={!sidebarOpen} />
          ))}

          {projectNav.length > 0 && (
            <>
              <div className={`pt-4 pb-1 ${sidebarOpen ? 'px-3' : 'flex justify-center'}`}>
                {sidebarOpen ? (
                  <p className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
                    {activeProject?.name || 'Project'}
                  </p>
                ) : (
                  <div className="w-6 border-t" style={{ borderColor: 'var(--border-subtle)' }} />
                )}
              </div>
              {projectNav.map((item) => (
                <NavItem key={item.to} item={item} active={isActive(item)} collapsed={!sidebarOpen} />
              ))}
            </>
          )}
        </nav>

        {/* User section */}
        <div className="shrink-0 p-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className={`w-full flex items-center gap-3 p-2 rounded-lg transition-colors hover:bg-white/5 group ${!sidebarOpen && 'justify-center'}`}
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
                style={{ background: 'linear-gradient(135deg, var(--accent-violet), var(--accent-blue))' }}
              >
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              {sidebarOpen && (
                <div className="flex-1 text-left overflow-hidden">
                  <p className="text-sm font-medium text-white truncate">{user?.name || 'User'}</p>
                  <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{user?.email || ''}</p>
                </div>
              )}
            </button>

            {userMenuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                <div
                  className="absolute bottom-full left-0 mb-1 w-48 rounded-xl border shadow-2xl overflow-hidden z-50"
                  style={{ background: 'var(--surface-1)', borderColor: 'var(--border-default)' }}
                >
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut size={16} />
                    Sign out
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* ─── Main content ─── */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        {/* Topbar */}
        <header
          className="h-16 shrink-0 flex items-center justify-between px-6"
          style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(3,7,18,0.5)', backdropFilter: 'blur(12px)' }}
        >
          {/* Breadcrumbs */}
          <nav className="flex items-center gap-1 text-sm">
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <ChevronRight size={14} className="text-slate-700 mx-0.5" />}
                {crumb.to && idx < breadcrumbs.length - 1 ? (
                  <Link to={crumb.to} className="text-slate-500 hover:text-white transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-slate-300 font-medium">{crumb.label}</span>
                )}
              </React.Fragment>
            ))}
          </nav>

          {/* Status indicator */}
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
            style={{ background: 'var(--surface-1)', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            System Online
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

const NavItem = ({ item, active, collapsed }) => {
  const Icon = item.icon;
  return (
    <Link
      to={item.to}
      title={collapsed ? item.label : undefined}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative
        ${collapsed && 'justify-center px-0'}
      `}
      style={{
        background: active ? 'rgba(139,92,246,0.15)' : 'transparent',
        border: active ? '1px solid rgba(139,92,246,0.3)' : '1px solid transparent',
        color: active ? 'var(--accent-violet-light)' : 'var(--text-secondary)',
      }}
      onMouseEnter={e => !active && (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
      onMouseLeave={e => !active && (e.currentTarget.style.background = 'transparent')}
    >
      <Icon size={18} className="shrink-0" style={{ color: active ? 'var(--accent-violet-light)' : 'var(--text-muted)' }} />
      {!collapsed && <span className="truncate flex-1">{item.label}</span>}
      {active && !collapsed && (
        <span className="w-1.5 h-1.5 rounded-full ml-auto" style={{ background: 'var(--accent-violet-light)' }} />
      )}
    </Link>
  );
};

export default Shell;

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { projectApi } from '../services/api';
import useStore from '../store/useStore';
import { Activity, Database, FileCode2, Play, Users, GitBranch, TerminalSquare, Loader2 } from 'lucide-react';

const ProjectPage = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const setActiveProject = useStore(state => state.setActiveProject);

  useEffect(() => {
    const loadProject = async () => {
      try {
        const res = await projectApi.get(projectId);
        setProject(res.data);
        setActiveProject(res.data);
      } catch (error) {
        console.error("Failed to load project details", error);
      } finally {
        setIsLoading(false);
      }
    };
    loadProject();
  }, [projectId, setActiveProject]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={32} className="text-violet-500 animate-spin" />
      </div>
    );
  }

  if (!project) return <div className="text-slate-400">Project not found</div>;

  const stats = [
    { label: 'Files Generated', value: project.stats?.files || 0, icon: FileCode2, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'Agent Runs', value: project.stats?.agent_runs || 0, icon: Activity, color: 'text-violet-400', bg: 'bg-violet-400/10' },
    { label: 'Key Decisions', value: project.stats?.decisions || 0, icon: GitBranch, color: 'text-amber-400', bg: 'bg-amber-400/10' },
    { label: 'Active Agents', value: 5, icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header Area */}
      <div className="glass-panel p-8 rounded-2xl border border-slate-700/50 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        
        <div className="relative z-10 flex justify-between items-start">
          <div>
            <div className="inline-block px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300 uppercase tracking-wider mb-4">
              {project.status.replace('_', ' ')}
            </div>
            <h1 className="text-4xl font-bold text-white tracking-tight mb-4">{project.name}</h1>
            <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
              {project.description || "No description provided. Trigger the Planner Agent to generate a PRD."}
            </p>
          </div>
          
          <Link 
            to={`/project/${projectId}/workspace`}
            className="bg-violet-600 hover:bg-violet-500 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg shadow-violet-600/20 flex items-center gap-2 hover:-translate-y-0.5"
          >
            <Play size={18} className="fill-current" />
            Launch Agents
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => (
          <div key={idx} className="glass-panel p-6 rounded-xl border border-slate-700/50 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${stat.bg} ${stat.color} border border-current/20`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
              <p className="text-sm font-medium text-slate-400">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link to={`/project/${projectId}/workspace`} className="group glass-panel p-6 rounded-xl border border-slate-700/50 hover:border-violet-500/50 transition-all">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-10 h-10 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 group-hover:bg-violet-500/20 transition-colors">
              <TerminalSquare size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white group-hover:text-violet-400 transition-colors">Agent Workspace</h3>
          </div>
          <p className="text-slate-400 text-sm">Chat with the AI team, trigger workflows, and watch code generation in real-time.</p>
        </Link>

        <Link to={`/project/${projectId}/memory`} className="group glass-panel p-6 rounded-xl border border-slate-700/50 hover:border-blue-500/50 transition-all">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:bg-blue-500/20 transition-colors">
              <Database size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">Memory & Decisions</h3>
          </div>
          <p className="text-slate-400 text-sm">Review architectural decisions, knowledge graph, and past project context.</p>
        </Link>
      </div>
    </div>
  );
};

export default ProjectPage;

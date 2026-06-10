import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Loader2, Code2, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { projectApi } from '../services/api';
import useStore from '../store/useStore';

const DashboardPage = () => {
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const navigate = useNavigate();
  const setActiveProject = useStore(state => state.setActiveProject);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list();
      setProjects(res.data);
    } catch (error) {
      console.error('Failed to fetch projects', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    
    setIsCreating(true);
    try {
      const res = await projectApi.create({
        name: newProjectName,
        description: newProjectDesc,
      });
      setProjects([res.data, ...projects]);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      
      // Optionally navigate directly to the new project
      handleOpenProject(res.data);
    } catch (error) {
      console.error('Failed to create project', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleOpenProject = (project) => {
    setActiveProject(project);
    navigate(`/project/${project.id}`);
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'planning': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      case 'in_progress': return 'text-violet-400 bg-violet-400/10 border-violet-400/20';
      case 'review': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
      case 'deployed': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
    }
  };

  return (
    <div className="max-w-6xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Your Projects</h2>
          <p className="text-slate-400 mt-1">Manage your AI-engineered applications</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 shadow-lg shadow-violet-500/20"
        >
          <Plus size={18} />
          New Project
        </button>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 size={32} className="text-violet-500 animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center glass-panel rounded-2xl border border-slate-700/50 p-12 text-center">
          <div className="w-20 h-20 bg-slate-800 rounded-2xl flex items-center justify-center mb-6 border border-slate-700">
            <Code2 size={40} className="text-slate-500" />
          </div>
          <h3 className="text-xl font-medium text-white mb-2">No projects yet</h3>
          <p className="text-slate-400 max-w-md mb-8">
            Create your first project and let the BuildX AI Engineering team bring it to life.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-xl font-medium transition-colors flex items-center gap-2 border border-slate-600"
          >
            <Plus size={18} />
            Create Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div 
              key={project.id}
              onClick={() => handleOpenProject(project)}
              className="glass-panel rounded-xl p-6 border border-slate-700/50 hover:border-violet-500/50 hover:shadow-[0_0_20px_rgba(124,58,237,0.1)] transition-all cursor-pointer group flex flex-col h-64"
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`px-2.5 py-1 rounded-md border text-xs font-medium uppercase tracking-wider ${getStatusColor(project.status)}`}>
                  {project.status.replace('_', ' ')}
                </div>
                <button className="text-slate-500 hover:text-white transition-colors opacity-0 group-hover:opacity-100">
                  <ArrowRight size={20} />
                </button>
              </div>
              
              <h3 className="text-xl font-bold text-white mb-2 line-clamp-1 group-hover:text-violet-400 transition-colors">
                {project.name}
              </h3>
              
              <p className="text-slate-400 text-sm line-clamp-3 mb-6 flex-1">
                {project.description || 'No description provided.'}
              </p>
              
              <div className="mt-auto pt-4 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-500 font-medium">
                <div className="flex items-center gap-1.5">
                  <Clock size={14} />
                  <span>{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
                {project.status === 'deployed' && (
                  <div className="flex items-center gap-1.5 text-emerald-500">
                    <CheckCircle2 size={14} />
                    <span>Active</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-md rounded-2xl p-6 border border-slate-700 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-blue-500" />
            
            <h2 className="text-xl font-bold text-white mb-6">Create New Project</h2>
            
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Project Name</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-all"
                  placeholder="e.g. Acme CRM"
                  autoFocus
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Description (Optional)</label>
                <textarea
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-all resize-none h-24"
                  placeholder="A brief description of what you want to build..."
                />
              </div>

              <div className="flex gap-3 mt-8">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2.5 rounded-lg font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !newProjectName.trim()}
                  className="flex-1 bg-violet-600 hover:bg-violet-500 text-white px-4 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isCreating ? <Loader2 size={18} className="animate-spin" /> : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Database, GitBranch, TerminalSquare, Loader2, Search, BrainCircuit } from 'lucide-react';
import { memoryApi, projectApi } from '../services/api';

const MemoryPage = () => {
  const { projectId } = useParams();
  const [decisions, setDecisions] = useState([]);
  const [memories, setMemories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [decisionsRes, memoriesRes] = await Promise.all([
        projectApi.getDecisions(projectId),
        memoryApi.list(projectId)
      ]);
      setDecisions(decisionsRes.data);
      setMemories(memoriesRes.data);
    } catch (error) {
      console.error('Failed to fetch memory data', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    
    try {
      const res = await memoryApi.search(projectId, searchQuery);
      setSearchResults(res.data);
    } catch (error) {
      console.error('Search failed', error);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={32} className="text-violet-500 animate-spin" />
      </div>
    );
  }

  const renderContent = (content) => {
    // Simple markdown-ish rendering for MVP
    return content.split('\n').map((line, i) => (
      <p key={i} className="mb-2">{line}</p>
    ));
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <BrainCircuit className="text-blue-400" size={32} />
            Project Memory
          </h2>
          <p className="text-slate-400 mt-1">
            Review architectural decisions and semantic context stored by the AI agents.
          </p>
        </div>
        
        {/* Semantic Search Bar */}
        <form onSubmit={handleSearch} className="relative w-96">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Semantic search across memory..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
          />
        </form>
      </div>

      {searchResults && (
        <div className="glass-panel p-6 rounded-2xl border border-blue-500/50 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Search size={20} className="text-blue-400" />
              Search Results
            </h3>
            <button 
              onClick={() => { setSearchQuery(''); setSearchResults(null); }}
              className="text-sm text-slate-400 hover:text-white"
            >
              Clear
            </button>
          </div>
          <div className="space-y-4">
            {searchResults.length === 0 ? (
              <p className="text-slate-400">No matching context found.</p>
            ) : (
              searchResults.map((res) => (
                <div key={res.id} className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
                  <div className="flex gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                      {res.type}
                    </span>
                    <span className="text-xs text-slate-500">
                      Score: {res.score?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                  <h4 className="font-semibold text-white mb-2">{res.title}</h4>
                  <div className="text-sm text-slate-300">
                    {renderContent(res.content)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Architectural Decisions */}
        <section>
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
              <GitBranch size={20} className="text-amber-400" />
            </div>
            <h3 className="text-xl font-bold text-white">Architectural Decisions</h3>
          </div>
          
          <div className="space-y-4">
            {decisions.length === 0 ? (
              <div className="glass-panel p-8 rounded-2xl text-center text-slate-400 border border-slate-700/50">
                No architectural decisions recorded yet. Run the Architect agent.
              </div>
            ) : (
              decisions.map((decision) => (
                <div key={decision.id} className="glass-panel p-6 rounded-2xl border border-slate-700/50 hover:border-amber-500/30 transition-colors">
                  <h4 className="text-lg font-bold text-white mb-3">{decision.title}</h4>
                  <div className="bg-slate-900/50 rounded-lg p-4 mb-4 text-sm text-slate-300 border border-slate-700/50">
                    <strong className="text-slate-400 block mb-1">Rationale:</strong>
                    {renderContent(decision.rationale)}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {decision.tags?.map(tag => (
                      <span key={tag} className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50 text-xs text-slate-500 font-medium">
                    Recorded on {new Date(decision.created_at).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* General Memories */}
        <section>
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center border border-violet-500/20">
              <TerminalSquare size={20} className="text-violet-400" />
            </div>
            <h3 className="text-xl font-bold text-white">General Context & Learnings</h3>
          </div>
          
          <div className="space-y-4">
            {memories.length === 0 ? (
              <div className="glass-panel p-8 rounded-2xl text-center text-slate-400 border border-slate-700/50">
                No memories recorded yet. Agents will consolidate memory automatically.
              </div>
            ) : (
              memories.filter(m => m.type !== 'decision').map((memory) => (
                <div key={memory.id} className="glass-panel p-6 rounded-2xl border border-slate-700/50 hover:border-violet-500/30 transition-colors">
                  <div className="flex gap-2 mb-3">
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-violet-500/10 text-violet-400 border border-violet-500/20 uppercase tracking-wider">
                      {memory.type}
                    </span>
                  </div>
                  {memory.title && <h4 className="font-semibold text-white mb-2">{memory.title}</h4>}
                  <div className="text-sm text-slate-300 prose prose-invert max-w-none">
                    {renderContent(memory.content)}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {memory.tags?.map(tag => (
                      <span key={tag} className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

      </div>
    </div>
  );
};

export default MemoryPage;

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { Send, Play, Terminal, Bot, Code2, Loader2, RefreshCw, CheckCircle2 } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { agentApi, projectApi } from '../services/api';

const AgentWorkspacePage = () => {
  const { projectId } = useParams();
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('planner');
  const [activeFile, setActiveFile] = useState(null);
  const [fileContent, setFileContent] = useState('// Select a file or run an agent to see generated code');
  const [files, setFiles] = useState([]);
  const [isDeploying, setIsDeploying] = useState(false);
  
  const { messages, isConnected, sendMessage } = useWebSocket(projectId);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetchFiles();
  }, [projectId]);

  const fetchFiles = async () => {
    try {
      const res = await projectApi.getFiles(projectId);
      setFiles(res.data);
    } catch (error) {
      console.error('Failed to fetch files', error);
    }
  };

  const handleRunAgent = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    try {
      if (selectedAgent === 'workflow') {
        await agentApi.runWorkflow(projectId, input);
        sendMessage('chat', { message: `Started full workflow with input: ${input}` });
      } else {
        await agentApi.runAgent(projectId, selectedAgent, input);
        sendMessage('chat', { message: `Started ${selectedAgent} with input: ${input}` });
      }
      setInput('');
    } catch (error) {
      console.error('Failed to run agent', error);
    }
  };

  const loadFile = async (path) => {
    try {
      const res = await projectApi.getFileContent(projectId, path);
      setActiveFile(path);
      setFileContent(res.data.content);
    } catch (error) {
      console.error('Failed to load file', error);
    }
  };

  const getLanguageFromPath = (path) => {
    if (!path) return 'javascript';
    if (path.endsWith('.py')) return 'python';
    if (path.endsWith('.js') || path.endsWith('.jsx')) return 'javascript';
    if (path.endsWith('.ts') || path.endsWith('.tsx')) return 'typescript';
    if (path.endsWith('.md')) return 'markdown';
    if (path.endsWith('.json')) return 'json';
    if (path.endsWith('.html')) return 'html';
    if (path.endsWith('.css')) return 'css';
    return 'plaintext';
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6">
      
      {/* Chat & Agent Control Panel */}
      <div className="w-1/3 flex flex-col gap-4">
        
        {/* Controls */}
        <div className="glass-panel p-4 rounded-xl border border-slate-700/50 shrink-0">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Bot size={18} className="text-violet-400" />
              Agent Command
            </h3>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]' : 'bg-red-500'}`} />
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">
                {isConnected ? 'Connected' : 'Offline'}
              </span>
            </div>
          </div>
          
          <form onSubmit={handleRunAgent} className="space-y-3">
            <select 
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-violet-500"
            >
              <option value="workflow">▶ Full Auto Workflow (Planner → Deploy)</option>
              <option value="planner">🧠 Planner Agent (Requirements)</option>
              <option value="architect">🏗️ Architect Agent (System Design)</option>
              <option value="frontend">🎨 Frontend Agent (React/UI)</option>
              <option value="backend_dev">⚙️ Backend Agent (Django/API)</option>
              <option value="reviewer">🔍 Reviewer Agent (Code Quality)</option>
            </select>
            
            <div className="relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="What should we build or change?"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500 resize-none h-24"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleRunAgent(e);
                  }
                }}
              />
              <button 
                type="submit"
                disabled={!input.trim()}
                className="absolute bottom-2 right-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 text-white p-1.5 rounded-md transition-colors"
              >
                <Send size={16} />
              </button>
            </div>
          </form>
        </div>

        {/* Streaming Feed */}
        <div className="glass-panel rounded-xl border border-slate-700/50 flex-1 flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/50 flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2 text-sm">
              <Terminal size={16} className="text-slate-400" />
              Activity Feed
            </h3>
            {messages.length > 0 && (
              <span className="text-xs text-slate-500 animate-pulse flex items-center gap-1">
                <RefreshCw size={12} className="animate-spin" /> active
              </span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm text-center px-4">
                <Bot size={24} className="mb-2 opacity-50" />
                <p>No activity yet. Trigger an agent to start building.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className="flex gap-3 text-sm animate-in fade-in slide-in-from-bottom-2">
                  <div className={`w-6 h-6 rounded flex items-center justify-center shrink-0 mt-0.5 ${
                    msg.type === 'agent_complete' ? 'bg-emerald-500/20 text-emerald-400' : 
                    msg.type === 'error' ? 'bg-red-500/20 text-red-400' :
                    'bg-violet-500/20 text-violet-400'
                  }`}>
                    {msg.type === 'agent_complete' ? <CheckCircle2 size={14} /> : <Bot size={14} />}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-baseline gap-2">
                      <span className="font-semibold text-slate-200 capitalize">{msg.agent || 'System'}</span>
                      <span className="text-xs text-slate-500">{msg.type}</span>
                    </div>
                    <div className="text-slate-300 bg-slate-900/50 p-2.5 rounded-lg border border-slate-700/50 font-mono text-xs whitespace-pre-wrap">
                      {msg.output || msg.message || msg.content}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>
        </div>
      </div>

      {/* Editor & File Explorer */}
      <div className="flex-1 flex flex-col glass-panel rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="h-12 border-b border-slate-700/50 bg-slate-800/50 flex items-center px-2">
          {/* File Tabs */}
          <div className="flex-1 flex items-center overflow-x-auto gap-1 px-2 hide-scrollbar">
            {files.map(f => (
              <button
                key={f.path}
                onClick={() => loadFile(f.path)}
                className={`px-3 py-1.5 rounded-t-lg text-sm font-medium flex items-center gap-2 border-t border-x border-transparent transition-colors whitespace-nowrap ${
                  activeFile === f.path 
                    ? 'bg-[#1e1e1e] text-violet-400 border-slate-700/50 border-b-transparent' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
                }`}
              >
                <Code2 size={14} />
                {f.path.split('/').pop()}
              </button>
            ))}
            {files.length === 0 && (
              <span className="text-sm text-slate-500 italic px-2">No files generated yet</span>
            )}
          </div>
          
          <button 
            onClick={fetchFiles}
            className="p-1.5 text-slate-400 hover:text-white rounded transition-colors ml-2"
            title="Refresh Files"
          >
            <RefreshCw size={14} />
          </button>
        </div>
        
        <div className="flex-1 bg-[#1e1e1e]">
          <Editor
            height="100%"
            theme="vs-dark"
            path={activeFile || 'welcome.js'}
            language={getLanguageFromPath(activeFile)}
            value={fileContent}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              padding: { top: 16 },
              scrollBeyondLastLine: false,
              smoothScrolling: true,
              cursorBlinking: "smooth",
              renderLineHighlight: "all",
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default AgentWorkspacePage;

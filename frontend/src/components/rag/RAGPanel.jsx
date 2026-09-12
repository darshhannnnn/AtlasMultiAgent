import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { useAgentStore } from '../../store/useAgentStore';
import DocumentUpload from './DocumentUpload';
import ChunkViewer from './ChunkViewer';
import GlassCard from '../ui/GlassCard';
import { Search, Database, Sparkles, BookOpen, Layers, ChevronDown } from 'lucide-react';
import MarkdownFormatter from '../ui/MarkdownFormatter';

export const RAGPanel = () => {
  const { apiKey, selectedProvider, selectedModel } = useAppStore();
  const { setNodeActive, clearActiveNodes } = useAgentStore();

  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(4);
  const [localProvider, setLocalProvider] = useState(selectedProvider || 'google');
  const [localModel, setLocalModel] = useState(selectedModel || 'gemini-flash-lite-latest');
  
  const [answer, setAnswer] = useState('');
  const [chunks, setChunks] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Sync with global store when backend config is loaded
  React.useEffect(() => {
    if (selectedProvider) setLocalProvider(selectedProvider);
    if (selectedModel) setLocalModel(selectedModel);
  }, [selectedProvider, selectedModel]);

  // Default models map for local override
  const handleProviderChange = (provider) => {
    setLocalProvider(provider);
    if (provider === 'google') setLocalModel('gemini-flash-lite-latest');
    else if (provider === 'openai') setLocalModel('gpt-4o-mini');
    else if (provider === 'anthropic') setLocalModel('claude-3-5-sonnet-20240620');
    else if (provider === 'groq') setLocalModel('llama-3.1-8b-instant');
    else if (provider === 'openrouter') setLocalModel('openai/gpt-4o-mini');
    else if (provider === 'ollama') setLocalModel('llama3');
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setAnswer('');
    
    setNodeActive('rag_agent', true);
    setNodeActive('chromadb', true);
    setNodeActive('orchestrator', true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          top_k: parseInt(topK),
          provider: localProvider,
          model: localModel,
          api_key: (apiKey && apiKey.trim()) ? apiKey.trim() : null
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Search request failed.');
      }
      const data = await response.json();
      
      setAnswer(data.answer);
      setChunks(data.chunks || []);
    } catch (error) {
      console.error(error);
      setAnswer(`Failed to query RAG agent. ${error.message}`);
      setChunks([]);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        clearActiveNodes();
      }, 1500);
    }
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row gap-6 p-6 h-full overflow-hidden">
      
      {/* Left Column: Upload & Query Controls */}
      <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-1">
        
        {/* Upload Zone */}
        <GlassCard className="p-5! rounded-2xl">
          <div className="flex items-center gap-2 mb-4 text-xs font-bold text-stone-500 tracking-wider uppercase font-mono">
            <Database className="h-4 w-4 text-beige-600" />
            <span>Document Ingestion</span>
          </div>
          <DocumentUpload onUploadSuccess={() => {}} />
        </GlassCard>

        {/* Query Console */}
        <GlassCard className="p-5! rounded-2xl flex-1 flex flex-col">
          <div className="flex items-center gap-2 mb-4 text-xs font-bold text-stone-500 tracking-wider uppercase font-mono">
            <Search className="h-4 w-4 text-beige-600" />
            <span>Query Knowledge Base</span>
          </div>

          <form onSubmit={handleSearch} className="flex flex-col gap-4 mb-6">
            
            {/* Input and submit */}
            <div className="relative flex items-center">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search matching document chunks..."
                className="w-full bg-white/40 border border-white/50 backdrop-blur-md rounded-xl pl-5 pr-12 py-3 text-xs text-stone-800 focus:outline-none focus:border-beige-400 font-sans"
              />
              <button
                type="submit"
                disabled={!query.trim() || isLoading}
                className="absolute right-2.5 p-2 rounded-lg bg-beige-500 hover:bg-beige-400 text-white disabled:opacity-50 transition-all shadow-[0_2px_8px_rgba(168,152,120,0.2)]"
              >
                {isLoading ? <Sparkles className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
              </button>
            </div>

            {/* Custom per-query model & config selectors */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-[9px] font-bold text-stone-500 uppercase tracking-wider font-mono">Provider</label>
                <div className="relative flex items-center">
                  <select
                    value={localProvider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                    className="w-full bg-white/40 border border-white/50 backdrop-blur-md text-stone-800 text-[11px] rounded-lg pl-2 pr-7 py-1.5 focus:outline-none focus:border-beige-400 cursor-pointer appearance-none"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google Gemini</option>
                    <option value="groq">Groq</option>
                    <option value="openrouter">OpenRouter</option>
                    <option value="ollama">Ollama (Local)</option>
                  </select>
                  <ChevronDown className="absolute right-2 h-3 w-3 text-stone-500 pointer-events-none" />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[9px] font-bold text-stone-500 uppercase tracking-wider font-mono">Model Name</label>
                <input
                  type="text"
                  value={localModel}
                  onChange={(e) => setLocalModel(e.target.value)}
                  className="bg-white/40 border border-white/50 backdrop-blur-md text-stone-800 text-[11px] rounded-lg px-2 py-1.5 focus:outline-none focus:border-beige-400 font-mono"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[9px] font-bold text-stone-500 uppercase tracking-wider font-mono">Top-k Chunks</label>
                <div className="relative flex items-center">
                  <select
                    value={topK}
                    onChange={(e) => setTopK(e.target.value)}
                    className="w-full bg-white/40 border border-white/50 backdrop-blur-md text-stone-800 text-[11px] rounded-lg pl-2 pr-7 py-1.5 focus:outline-none focus:border-beige-400 cursor-pointer appearance-none"
                  >
                    <option value={2}>2 Chunks</option>
                    <option value={4}>4 Chunks</option>
                    <option value={6}>6 Chunks</option>
                    <option value={8}>8 Chunks</option>
                  </select>
                  <ChevronDown className="absolute right-2 h-3 w-3 text-stone-500 pointer-events-none" />
                </div>
              </div>
            </div>
          </form>

          {/* Answer Display */}
          <div className="flex-1 flex flex-col">
            <div className="text-[11px] font-bold text-stone-500 tracking-wider uppercase font-mono mb-2 flex items-center gap-1.5">
              <BookOpen className="h-3.5 w-3.5 text-beige-600" />
              <span>LLM Generated Response</span>
            </div>
            <div className="flex-1 bg-stone-50 border border-stone-200 rounded-xl p-4 overflow-y-auto text-xs text-stone-800 leading-relaxed font-sans select-text">
              {isLoading ? (
                <div className="flex items-center gap-2 text-stone-400 italic">
                  <Sparkles className="h-3.5 w-3.5 animate-spin" />
                  <span>Synthesizing retrieval answer...</span>
                </div>
              ) : answer ? (
                <MarkdownFormatter text={answer} />
              ) : (
                <span className="text-stone-400 italic">Submit a search query above to synthesize answers from indexed contexts.</span>
              )}
            </div>
          </div>

        </GlassCard>

      </div>

      {/* Right Column: Chunk Viewer */}
      <div className="w-full md:w-[380px] shrink-0 h-full overflow-hidden flex flex-col">
        <GlassCard className="h-full p-5! flex flex-col rounded-2xl">
          <ChunkViewer chunks={chunks} />
        </GlassCard>
      </div>

    </div>
  );
};

export default RAGPanel;

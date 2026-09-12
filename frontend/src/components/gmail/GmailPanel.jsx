import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { useAgentStore } from '../../store/useAgentStore';
import EmailList from './EmailList';
import SummaryCard from './SummaryCard';
import GlassCard from '../ui/GlassCard';
import { Mail, Sparkles, LogIn, RefreshCw, Check } from 'lucide-react';

export const GmailPanel = () => {
  const { apiKey, activeProvider, modelName } = useAppStore();
  const { setNodeActive, clearActiveNodes } = useAgentStore();

  const [connected, setConnected] = useState(false);
  const [emails, setEmails] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  
  const [activeEmail, setActiveEmail] = useState(null);
  const [summary, setSummary] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);

  const [labelFilter, setLabelFilter] = useState('INBOX');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchEmailsList = async () => {
    setIsLoading(true);
    setNodeActive('gmail_agent', true);

    try {
      // Build query string params
      let url = `http://localhost:8000/api/v1/gmail/list?max_results=12&label=${labelFilter}`;
      if (searchQuery.trim()) {
        url += `&q=${encodeURIComponent(searchQuery.trim())}`;
      }

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) {
          setEmails(data);
          setConnected(true);
        } else {
          // If error text string is returned
          console.warn('OAuth credentials validation returned error string:', data);
          setConnected(false);
        }
      } else {
        setConnected(false);
      }
    } catch (error) {
      console.warn('Connection offline or unauthorized. Gmail oauth file missing.', error);
      setConnected(false);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        clearActiveNodes();
      }, 1500);
    }
  };

  // Attempt to check if OAuth tokens exist
  useEffect(() => {
    fetchEmailsList();
  }, [labelFilter, searchQuery]);

  const handleConnect = async () => {
    setIsLoading(true);
    setNodeActive('gmail_agent', true);

    try {
      // InstalledAppFlow initiates local browser window login popup
      const response = await fetch('http://localhost:8000/api/v1/gmail/list?max_results=5');
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) {
          setEmails(data);
          setConnected(true);
        } else {
          alert(`Gmail connection warning: ${data}`);
        }
      } else {
        let errorMsg = 'Credentials file credentials.json not found in server root. Please add it to start OAuth.';
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errorMsg = errData.detail;
          }
        } catch (_) {}
        alert(`Gmail connection error: ${errorMsg}`);
      }
    } catch (error) {
      alert(`Gmail connection error: ${error.message}`);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        clearActiveNodes();
      }, 1000);
    }
  };

  // Summarize single email
  const handleSummarizeSingle = async (msgId) => {
    setIsSummarizing(true);
    setNodeActive('gmail_agent', true);
    setNodeActive('orchestrator', true);
    setSummary('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/gmail/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_ids: [msgId],
          provider: activeProvider,
          model: modelName,
          api_key: (apiKey && apiKey.trim()) ? apiKey.trim() : null
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Summarize query failed.');
      }
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error(error);
      setSummary(`Summary failed: ${error.message}`);
    } finally {
      setIsSummarizing(false);
      setTimeout(() => {
        clearActiveNodes();
      }, 1500);
    }
  };

  // Bulk summarize multiple selected checkmarked emails
  const handleBulkSummarize = async () => {
    if (selectedIds.length === 0) return;
    
    setIsSummarizing(true);
    setNodeActive('gmail_agent', true);
    setNodeActive('orchestrator', true);
    setActiveEmail(null); // Clear selected single email to show general bulk summary
    setSummary('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/gmail/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_ids: selectedIds,
          provider: activeProvider,
          model: modelName,
          api_key: (apiKey && apiKey.trim()) ? apiKey.trim() : null
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Bulk summarize request failed.');
      }
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error(error);
      setSummary(`Bulk summary failed: ${error.message}`);
    } finally {
      setIsSummarizing(false);
      setTimeout(() => {
        clearActiveNodes();
      }, 1500);
    }
  };

  const handleEmailClick = (email) => {
    setActiveEmail(email);
    setSummary(''); // Clear previous summary so they can generate for this new one
  };

  // If not authenticated, show OAuth flow landing page
  if (!connected) {
    return (
      <div className="flex-1 flex items-center justify-center p-6 h-full">
        <GlassCard className="max-w-md w-full p-8! text-center flex flex-col items-center rounded-3xl border-stone-200 bg-white/70">
          <div className="p-4 rounded-full bg-beige-150 mb-6 border border-beige-200">
            <Mail className="h-10 w-10 text-beige-600" />
          </div>

          <h2 className="text-xl font-bold text-stone-900 mb-2 font-sans tracking-wide">
            Gmail Agent Integration
          </h2>
          
          <p className="text-xs text-stone-600 leading-relaxed mb-6 font-sans">
            Connect your Google Workspace or Gmail Account. Nass Agent requires a valid Google OAuth OAuth2 consent validation to securely view messages.
          </p>

          <button
            onClick={handleConnect}
            disabled={isLoading}
            className="flex items-center justify-center gap-2.5 w-full py-3 rounded-xl bg-gradient-to-r from-beige-400 to-beige-600 hover:from-beige-300 hover:to-beige-500 text-white font-semibold text-xs transition-all disabled:opacity-50 shadow-[0_4px_16px_rgba(168,152,120,0.2)]"
          >
            {isLoading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <LogIn className="h-4 w-4" />
            )}
            <span>Connect Google Account via OAuth2</span>
          </button>

          <p className="text-[10px] text-stone-500 mt-4 font-mono font-bold leading-normal">
            Note: Place credentials.json in the project root first.
          </p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col md:flex-row gap-6 p-6 h-full overflow-hidden">
      
      {/* Left Column: Email Rows list */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <GlassCard className="h-full p-5! flex flex-col rounded-2xl">
          <div className="flex items-center justify-between mb-4 shrink-0">
            <div className="flex items-center gap-2 text-xs font-bold text-stone-500 tracking-wider uppercase font-mono">
              <Mail className="h-4 w-4 text-beige-600" />
              <span>Inbox Navigator</span>
            </div>
            
            <button 
              onClick={fetchEmailsList}
              disabled={isLoading}
              className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-500 hover:text-stone-900 transition-colors"
              title="Refresh Inbox"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <EmailList 
            emails={emails}
            selectedIds={selectedIds}
            setSelectedIds={setSelectedIds}
            onEmailClick={handleEmailClick}
            onBulkSummarize={handleBulkSummarize}
            isLoading={isSummarizing}
            labelFilter={labelFilter}
            setLabelFilter={setLabelFilter}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
        </GlassCard>
      </div>

      {/* Right Column: Digest Summary Sidebar */}
      <div className="w-full md:w-[380px] shrink-0 h-full overflow-hidden flex flex-col">
        <SummaryCard 
          email={activeEmail}
          summary={summary}
          onSummarize={handleSummarizeSingle}
          isLoading={isSummarizing}
        />
      </div>

    </div>
  );
};

export default GmailPanel;

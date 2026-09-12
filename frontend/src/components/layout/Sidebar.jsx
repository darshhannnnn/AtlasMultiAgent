import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { MessageSquare, Database, Mail, Cpu, LogOut, Code } from 'lucide-react';

export const Sidebar = () => {
  const { activeSection, setActiveSection, user, logout } = useAppStore();

  const menuItems = [
    { id: 'chat', label: 'Chat Orchestrator', icon: MessageSquare },
    { id: 'rag', label: 'RAG Knowledge Base', icon: Database },
    { id: 'gmail', label: 'Gmail Agent', icon: Mail },
    { id: 'coding', label: 'Coding Workspace', icon: Code },
  ];

  return (
    <aside className="w-20 md:w-24 bg-white/35 backdrop-blur-2xl border-r border-white/50 flex flex-col items-center py-8 z-20 shrink-0 shadow-[2px_0_20px_rgba(168,152,120,0.06)]">
      {/* Brand Logo */}
      <div className="flex items-center justify-center p-3 rounded-2xl bg-gradient-to-tr from-beige-300 to-beige-500 shadow-[0_4px_16px_rgba(168,152,120,0.2)] mb-12 border border-white/40">
        <Cpu className="h-6 w-6 text-white animate-pulse" />
      </div>

      {/* Navigation List */}
      <nav className="flex-1 flex flex-col gap-6 w-full px-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              title={item.label}
              className={`relative group w-full py-4 flex flex-col items-center justify-center gap-1.5 rounded-2xl transition-all duration-300 ${
                isActive
                  ? 'text-stone-800 bg-white/40 shadow-[inset_0_1px_1px_rgba(255,255,255,0.6)] font-bold border border-white/50'
                  : 'text-stone-500 hover:text-stone-800 hover:bg-white/25'
              }`}
            >
              {isActive && (
                <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-gradient-to-b from-beige-300 to-beige-500 rounded-r-full" />
              )}

              <Icon className={`h-5 w-5 transition-transform duration-300 group-hover:scale-110 ${isActive ? 'text-beige-600' : ''}`} />
              <span className="text-[10px] scale-90 font-bold opacity-80 select-none">
                {item.id.toUpperCase()}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="flex flex-col items-center gap-3">
        {user && (
          <div className="flex flex-col items-center gap-2">
            {user.picture && (
              <img 
                src={user.picture} 
                alt={user.name} 
                className="h-7 w-7 rounded-full border border-stone-200/80 shadow-sm"
                referrerPolicy="no-referrer"
              />
            )}
            <button
              onClick={logout}
              title={`Sign out (${user.email})`}
              className="p-2.5 rounded-2xl text-stone-400 hover:text-rose-500 hover:bg-white/40 border border-transparent hover:border-white/50 transition-all duration-300"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
        <div className="text-stone-400 text-[10px] font-bold tracking-wider font-mono">
          v1.0
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

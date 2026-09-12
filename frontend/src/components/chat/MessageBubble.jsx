import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Cpu, Clock, Layers, User } from 'lucide-react';
import MarkdownFormatter from '../ui/MarkdownFormatter';

export const MessageBubble = ({ message }) => {
  const { role, content, model, tokens, latency } = message;
  const isUser = role === 'user';
  const { activeProvider } = useAppStore();

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-[75%] flex flex-col gap-2`}>
        {/* Card Bubble */}
        <div
          className={`rounded-2xl px-5 py-3.5 backdrop-blur-md border text-sm leading-relaxed ${
            isUser
              ? 'bg-gradient-to-tr from-beige-150 to-beige-200/50 border-beige-200/60 text-stone-900 shadow-[0_4px_16px_rgba(168,152,120,0.06)] rounded-tr-none'
              : 'bg-white/90 border-stone-200/60 text-stone-800 rounded-tl-none shadow-[0_4px_24px_rgba(0,0,0,0.04)]'
          }`}
        >
          <MarkdownFormatter text={content} />
        </div>

        {/* Info Badges */}
        <div className={`flex items-center gap-3 text-[10px] text-stone-500 font-mono select-none px-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {isUser ? (
            <div className="flex items-center gap-1">
              <User className="h-3 w-3 text-stone-400" />
              <span>You</span>
            </div>
          ) : (
            <>
              {/* Model Used Badge */}
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-stone-100/80 border border-stone-200/40">
                <Cpu className="h-2.5 w-2.5 text-beige-600" />
                <span>{model || 'system'}</span>
              </div>
              
              {/* Token Count Badge */}
              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-stone-100/80 border border-stone-200/40">
                <Layers className="h-2.5 w-2.5 text-beige-700" />
                <span>{tokens || 0} tokens</span>
              </div>

              {/* Latency Badge */}
              {latency && (
                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-stone-100/80 border border-stone-200/40">
                  <Clock className="h-2.5 w-2.5 text-beige-600" />
                  <span>{latency}s</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;

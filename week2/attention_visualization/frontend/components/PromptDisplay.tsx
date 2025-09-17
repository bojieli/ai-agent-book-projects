import React, { useState } from 'react';

interface PromptDisplayProps {
  prompt: string;
  tokens?: string[];
  tokenCount?: number;
}

export default function PromptDisplay({ prompt, tokens, tokenCount }: PromptDisplayProps) {
  const [showTokens, setShowTokens] = useState(false);

  // Use provided tokens if available, otherwise don't try to split
  const displayTokens = tokens || [];
  const hasTokens = displayTokens.length > 0;
  const actualTokenCount = tokenCount || displayTokens.length;

  return (
    <div className="card bg-blue-50 border-blue-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="section-title mb-0 text-blue-900">Prompt</h3>
        {hasTokens && (
          <button
            onClick={() => setShowTokens(!showTokens)}
            className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            {showTokens ? 'Show Text' : 'Show Tokens'} ({actualTokenCount} tokens)
          </button>
        )}
      </div>

      {showTokens && hasTokens ? (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {displayTokens.map((token, idx) => (
              <span
                key={idx}
                className="inline-block px-2 py-1 bg-blue-100 rounded text-sm font-mono hover:bg-blue-200 transition-colors cursor-default"
                title={`Token ${idx + 1}`}
              >
                {token}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="prose prose-sm max-w-none">
          <div className="bg-white/80 rounded-lg p-4 max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap font-sans text-gray-800 leading-relaxed">
              {prompt}
            </pre>
          </div>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-blue-200 flex justify-between text-sm text-blue-700">
        <span>Total Tokens: {actualTokenCount || 'N/A'}</span>
        <span>Characters: {prompt.length}</span>
      </div>
    </div>
  );
}

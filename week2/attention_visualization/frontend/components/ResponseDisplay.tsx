import React, { useState } from 'react';

interface ResponseDisplayProps {
  response: string;
  tokens: string[];
}

export default function ResponseDisplay({ response, tokens }: ResponseDisplayProps) {
  const [showTokens, setShowTokens] = useState(false);
  
  const hasTokens = tokens && tokens.length > 0;

  return (
    <div className="card bg-green-50 border-green-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="section-title mb-0 text-green-900">Model Response</h3>
        {hasTokens && (
          <button
            onClick={() => setShowTokens(!showTokens)}
            className="text-sm text-green-600 hover:text-green-700 transition-colors"
          >
            {showTokens ? 'Show Text' : 'Show Tokens'} ({tokens.length} tokens)
          </button>
        )}
      </div>

      {showTokens && hasTokens ? (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {tokens.map((token, idx) => (
              <span
                key={idx}
                className="inline-block px-2 py-1 bg-green-100 rounded text-sm font-mono hover:bg-green-200 transition-colors cursor-default"
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
              {response}
            </pre>
          </div>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-green-200 flex justify-between text-sm text-green-700">
        <span>Total Tokens: {hasTokens ? tokens.length : 'N/A'}</span>
        <span>Characters: {response.length}</span>
      </div>
    </div>
  );
}

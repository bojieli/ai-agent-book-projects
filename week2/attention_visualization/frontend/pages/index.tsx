import React, { useState, useEffect } from 'react';
import AttentionPreview from '@/components/AttentionPreview';
import AttentionModal from '@/components/AttentionModal';
import ResponseDisplay from '@/components/ResponseDisplay';
import PromptDisplay from '@/components/PromptDisplay';
import AttentionStats from '@/components/AttentionStats';

interface TestCase {
  category: string;
  query: string;
  description: string;
}

interface AttentionData {
  tokens: string[];
  attention_matrix: number[][];
  num_layers: number;
  num_heads: number;
}

interface LLMCall {
  step_num: number;
  step_type: string;
  prompt: string;  // Full prompt text
  response: string;  // Full response text
  tokens: string[];  // All tokens (input + output)
  input_tokens?: string[];  // Input tokens only
  output_tokens?: string[];  // Output tokens only
  input_token_count?: number;
  output_token_count?: number;
  total_token_count?: number;
  attention_data: AttentionData;
  tool_info?: any;
}

interface Trajectory {
  id: string;
  timestamp: string;
  test_case: TestCase;
  response: string;
  tokens: string[];
  attention_data: AttentionData;
  llm_calls?: LLMCall[];  // Multiple LLM calls for ReAct agents
  reasoning_steps?: any[];  // ReAct reasoning steps
  metadata: {
    model: string;
    temperature: number;
    max_tokens: number;
    device: string;
    total_llm_calls?: number;
    total_steps?: number;
    step_breakdown?: any;
  };
}

export default function Home() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trajectories, setTrajectories] = useState<Trajectory[]>([]);
  const [selectedTrajectoryIndex, setSelectedTrajectoryIndex] = useState(0);
  const [selectedLLMCallIndex, setSelectedLLMCallIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    loadTrajectories();
  }, []);

  const loadTrajectories = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try to fetch manifest file
      const manifestResponse = await fetch('/trajectories/manifest.json');
      
      if (!manifestResponse.ok) {
        // Try to load from a single results.json for backward compatibility
        try {
          const resultsResponse = await fetch('/results.json');
          if (resultsResponse.ok) {
            const data = await resultsResponse.json();
            setTrajectories(Array.isArray(data) ? data : [data]);
            return;
          }
        } catch (e) {
          // No results.json either
        }
        
        setError('No trajectory files found. Please run the agent first.');
        return;
      }
      
      const manifest = await manifestResponse.json();
      
      if (!manifest || manifest.length === 0) {
        setError('No trajectories in manifest. Please run the agent first.');
        return;
      }
      
      // Load each trajectory file from manifest
      const loadedTrajectories: Trajectory[] = [];
      for (const entry of manifest) {
        try {
          const trajResponse = await fetch(`/trajectories/${entry.filename}`);
          if (trajResponse.ok) {
            const trajData = await trajResponse.json();
            loadedTrajectories.push(trajData);
          }
        } catch (e) {
          console.error(`Failed to load ${entry.filename}:`, e);
        }
      }
      
      // Sort by timestamp (newest first)
      loadedTrajectories.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
      
      setTrajectories(loadedTrajectories);
      
      if (loadedTrajectories.length === 0) {
        setError('No valid trajectories could be loaded.');
      }
    } catch (err: any) {
      console.error('Failed to load trajectories:', err);
      setError(err.message || 'Failed to load trajectory files');
    } finally {
      setLoading(false);
    }
  };

  const currentTrajectory = trajectories[selectedTrajectoryIndex];
  const currentLLMCall = currentTrajectory?.llm_calls?.[selectedLLMCallIndex];
  
  // Use LLM call data if available, otherwise fall back to main trajectory data
  const displayData = currentLLMCall ? {
    prompt: currentLLMCall.prompt,  // Full prompt from LLM call
    response: currentLLMCall.response,  // Full response from LLM call
    tokens: currentLLMCall.output_tokens || currentLLMCall.tokens,  // Output tokens for response display
    input_tokens: currentLLMCall.input_tokens,  // Input tokens for prompt display
    attention_data: currentLLMCall.attention_data
  } : currentTrajectory ? {
    prompt: currentTrajectory.test_case.query,  // Use query as prompt if no LLM calls
    response: currentTrajectory.response,
    tokens: currentTrajectory.tokens,
    input_tokens: undefined,
    attention_data: currentTrajectory.attention_data
  } : null;

  const categoryColors: { [key: string]: string } = {
    'Math': 'bg-blue-100 text-blue-800 border-blue-300',
    'Knowledge': 'bg-green-100 text-green-800 border-green-300',
    'Reasoning': 'bg-purple-100 text-purple-800 border-purple-300',
    'Code': 'bg-orange-100 text-orange-800 border-orange-300',
    'Creative': 'bg-pink-100 text-pink-800 border-pink-300',
    'Tool Use': 'bg-indigo-100 text-indigo-800 border-indigo-300',
    'ReAct': 'bg-purple-100 text-purple-800 border-purple-300',
    'General': 'bg-gray-100 text-gray-800 border-gray-300',
    'Custom': 'bg-yellow-100 text-yellow-800 border-yellow-300'
  };

  const handleTrajectorySelect = (index: number) => {
    setSelectedTrajectoryIndex(index);
    setSelectedLLMCallIndex(0); // Reset to first LLM call when switching trajectories
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trajectories...</p>
        </div>
      </div>
    );
  }

  if (error && trajectories.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="card max-w-md">
          <div className="text-center">
            <svg className="h-12 w-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No Trajectories Found</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="bg-gray-50 rounded-lg p-4 text-left">
              <p className="text-sm text-gray-700 mb-2">To generate trajectories:</p>
              <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
                <li>Go to the project root directory</li>
                <li>Run: <code className="bg-gray-200 px-1 rounded">python main.py</code></li>
                <li>Refresh this page</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Attention Visualization
          </h1>
          <p className="text-gray-600">
            Explore how language models process information through attention mechanisms
          </p>
          {trajectories.length > 0 && (
            <p className="text-sm text-gray-500 mt-2">
              {trajectories.length} trajectory{trajectories.length !== 1 ? 'ies' : ''} loaded
            </p>
          )}
        </div>

        {/* Trajectory Tabs */}
        {trajectories.length > 1 && (
          <div className="mb-6">
            <div className="flex flex-wrap gap-2">
              {trajectories.map((traj, index) => {
                const colors = categoryColors[traj.test_case.category] || categoryColors['General'];
                return (
                  <button
                    key={traj.id}
                    onClick={() => handleTrajectorySelect(index)}
                    className={`px-4 py-2 rounded-lg border-2 transition-all ${
                      selectedTrajectoryIndex === index 
                        ? colors + ' font-semibold shadow-md transform scale-105'
                        : 'bg-white border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        selectedTrajectoryIndex === index ? '' : categoryColors[traj.test_case.category] || categoryColors['General']
                      }`}>
                        {traj.test_case.category}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(traj.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-sm mt-1 text-left">
                      {traj.test_case.query.length > 30 
                        ? traj.test_case.query.substring(0, 30) + '...' 
                        : traj.test_case.query}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Main Content */}
        {currentTrajectory && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Panel - Trajectory Info */}
            <div className="lg:col-span-1 space-y-4">
              <div className="card">
                <h3 className="section-title">Trajectory Details</h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wider">Category</label>
                    <div className={`inline-block px-3 py-1 rounded-full text-sm mt-1 ${
                      categoryColors[currentTrajectory.test_case.category] || categoryColors['General']
                    }`}>
                      {currentTrajectory.test_case.category}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wider">Timestamp</label>
                    <p className="text-sm text-gray-700 mt-1">{currentTrajectory.timestamp}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wider">Description</label>
                    <p className="text-sm text-gray-700 mt-1">{currentTrajectory.test_case.description}</p>
                  </div>
                </div>
              </div>

              {/* LLM Call Selector for ReAct agents */}
              {currentTrajectory.llm_calls && currentTrajectory.llm_calls.length > 1 && (
                <div className="card">
                  <h3 className="section-title">LLM Calls</h3>
                  <div className="space-y-2">
                    {currentTrajectory.llm_calls.map((call, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedLLMCallIndex(idx)}
                        className={`w-full text-left p-2 rounded transition-colors ${
                          selectedLLMCallIndex === idx
                            ? 'bg-primary-100 border-primary-500 border'
                            : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">
                            Step {call.step_num}: {call.step_type}
                          </span>
                          {call.attention_data?.attention_matrix?.length > 0 && (
                            <span className="text-xs text-gray-500">
                              {call.attention_data.attention_matrix.length} attn
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-600 mt-1 truncate">
                          {call.response.substring(0, 50)}...
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="card">
                <h3 className="section-title">Model Settings</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Model:</span>
                    <span className="font-medium">{currentTrajectory.metadata.model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Temperature:</span>
                    <span className="font-medium">{currentTrajectory.metadata.temperature}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Tokens:</span>
                    <span className="font-medium">{currentTrajectory.metadata.max_tokens}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Device:</span>
                    <span className="font-medium">{currentTrajectory.metadata.device}</span>
                  </div>
                  {currentTrajectory.metadata.total_llm_calls && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total LLM Calls:</span>
                      <span className="font-medium">{currentTrajectory.metadata.total_llm_calls}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Center/Right Panel - Visualization */}
            <div className="lg:col-span-2 space-y-4">
              {/* Query Display - Always show the original query first */}
              <div className="card bg-amber-50 border-amber-200">
                <h3 className="section-title mb-2 text-amber-900">User Query</h3>
                <div className="bg-white/80 rounded-lg p-4">
                  <pre className="whitespace-pre-wrap font-sans text-gray-800 leading-relaxed">
                    {currentTrajectory.test_case.query}
                  </pre>
                </div>
              </div>

              {/* Show current LLM call info if viewing a specific call */}
              {currentLLMCall && (
                <>
                  <div className="card bg-indigo-50 border-indigo-200">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-indigo-900">
                        LLM Call {currentLLMCall.step_num} - {currentLLMCall.step_type}
                      </h4>
                      <div className="flex items-center space-x-4 text-xs text-indigo-700">
                        <span>Input: {currentLLMCall.input_token_count || currentLLMCall.input_tokens?.length || 0} tokens</span>
                        <span>Output: {currentLLMCall.output_token_count || currentLLMCall.output_tokens?.length || 0} tokens</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Full Prompt Display */}
                  {currentLLMCall.prompt && (
                    <PromptDisplay 
                      prompt={currentLLMCall.prompt}
                      tokens={currentLLMCall.input_tokens}
                      tokenCount={currentLLMCall.input_token_count || currentLLMCall.input_tokens?.length}
                    />
                  )}
                </>
              )}

              {displayData && (
                <>
                  {/* Full Model Response Display */}
                  <ResponseDisplay 
                    response={displayData.response} 
                    tokens={displayData.tokens}  // Use output tokens for response
                  />
                  
                  {displayData.attention_data.attention_matrix.length > 0 && (
                    <>
                      <div className="card">
                        <h3 className="section-title mb-4">Attention Patterns</h3>
                        <div className="flex justify-center">
                          <AttentionPreview 
                            tokens={displayData.attention_data.tokens}
                            attentionWeights={displayData.attention_data.attention_matrix}
                            onClick={() => setIsModalOpen(true)}
                          />
                        </div>
                        <p className="text-center text-sm text-gray-600 mt-4">
                          Click the preview above to view the full attention pattern
                        </p>
                      </div>
                      
                      <AttentionModal
                        isOpen={isModalOpen}
                        onClose={() => setIsModalOpen(false)}
                        tokens={displayData.attention_data.tokens}
                        attentionWeights={displayData.attention_data.attention_matrix}
                      />
                    </>
                  )}
                  
                  <AttentionStats attentionData={displayData.attention_data} />
                </>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>To generate more trajectories, run: <code className="bg-gray-200 px-2 py-1 rounded">python agent.py</code> or <code className="bg-gray-200 px-2 py-1 rounded">python main.py</code></p>
        </div>
      </div>
    </div>
  );
}
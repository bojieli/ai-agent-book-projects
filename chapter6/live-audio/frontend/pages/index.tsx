import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Mic, MicOff, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface LogEntry {
  timestamp: number;
  message: string;
  type: 'info' | 'error' | 'latency' | 'llm';
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'transcript';
  content: string;
  isFinal?: boolean;
}

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

const CodeBlock = ({ node, inline, className, children, ...props }) => {
  const match = /language-(\w+)/.exec(className || '');
  const lang = match ? match[1] : '';
  
  if (!inline && lang) {
    return (
      <SyntaxHighlighter
        language={lang}
        style={oneDark}
        customStyle={{
          margin: '0.5em 0',
          borderRadius: '0.375rem',
          fontSize: '0.875rem',
        }}
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    );
  }

  return <code className={className} {...props}>{children}</code>;
};

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`flex-1 py-2 text-sm font-medium border-b-2 ${
      active 
        ? 'border-blue-500 text-blue-600' 
        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
    }`}
  >
    {children}
  </button>
);

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const websocketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const echoNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioFormatRef = useRef<any>(null);
  const speechEndTimeRef = useRef<number | null>(null);
  const llmStartTimeRef = useRef<number | null>(null);
  const vadEndTimeRef = useRef<number | null>(null);
  const hasPlaybackLatencyRef = useRef<boolean>(false);
  const vadStartTimeRef = useRef<number | null>(null);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const playbackStartTimeRef = useRef<number | null>(null);
  const [finalTranscripts, setFinalTranscripts] = useState<string>('');
  // Add this ref to track the current valid message ID
  const currentValidMessageIdRef = useRef<string | null>(null);
  // Add this ref to track if audio is currently playing
  const isPlayingRef = useRef<boolean>(false);
  // Add these refs after other refs
  const chatHistoryRef = useRef<HTMLDivElement>(null);
  const logsRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollChatRef = useRef(true);
  const shouldAutoScrollLogsRef = useRef(true);
  const [activeTab, setActiveTab] = useState<'chat' | 'logs'>('chat');

  const addLog = (message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [...prev, {
      timestamp: Date.now(),
      message,
      type
    }]);
  };

  const setupWebSocket = () => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) return;

    // Determine if we're running on localhost
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    let wsUrl;
    if (isLocalhost) {
      // For localhost development
      wsUrl = `ws://localhost:${process.env.WEBSOCKET_PORT}`;
    } else {
      // For production deployment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws`;
    }
    
    console.log('Connecting to WebSocket:', wsUrl);
    websocketRef.current = new WebSocket(wsUrl);
    websocketRef.current.binaryType = 'arraybuffer';

    websocketRef.current.onopen = () => {
      // Start sending pings when connection opens
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      pingIntervalRef.current = setInterval(() => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now()
          }));
        }
      }, 1000);
    };

    websocketRef.current.onmessage = async (event) => {
      try {
        if (event.data instanceof ArrayBuffer) {
          const now = Date.now();

          if (audioFormatRef.current) {
            const int16Array = new Int16Array(event.data);
            const float32Array = new Float32Array(int16Array.length);
            
            for (let i = 0; i < int16Array.length; i++) {
              float32Array[i] = int16Array[i] / 32768.0;
            }
            
            if (echoNodeRef.current) {
              // Set playback start time when first audio chunk is received
              if (!playbackStartTimeRef.current) {
                playbackStartTimeRef.current = Date.now();
              }

              echoNodeRef.current.port.postMessage({ type: 'unmute' });
              
              if (vadEndTimeRef.current && !hasPlaybackLatencyRef.current) {
                const latency = now - vadEndTimeRef.current;
                const serverVadLatency = now - (speechEndTimeRef.current || vadEndTimeRef.current);
                addLog(`First audio playback latency - Browser VAD: ${latency}ms`, 'latency');
                addLog(`First audio playback latency - Server VAD: ${serverVadLatency}ms`, 'latency');
                hasPlaybackLatencyRef.current = true;
              }
              echoNodeRef.current.port.postMessage(float32Array);
            }
          }
        } else {
          const jsonData = JSON.parse(event.data);
          const now = Date.now();
          
          // Add ping handling
          if (jsonData.type === 'pong') {
            const latency = now - jsonData.timestamp;
            addLog(`WebSocket latency: ${latency}ms`, 'latency');
            return;
          }

          switch (jsonData.type) {
            case 'speech_end':
              speechEndTimeRef.current = now;
              if (vadEndTimeRef.current) {
                const vadToServerLatency = now - vadEndTimeRef.current;
                addLog(`[Server] Speech end detected (${vadToServerLatency}ms after frontend VAD)`, 'latency');
              } else {
                // Use server's speech end as VAD end time if frontend didn't detect it
                vadEndTimeRef.current = now;
                hasPlaybackLatencyRef.current = false;
                addLog('[Server] Speech end detected (using as VAD endpoint)', 'latency');
              }
              break;

            case 'speech_start':
              // Handle interrupt
              handleInterrupt();
              // Clear audio queue and stop playback
              if (echoNodeRef.current) {
                echoNodeRef.current.port.postMessage({ type: 'clear' });
              }
              audioQueueRef.current = [];
              
              if (vadStartTimeRef.current) {
                const vadToServerLatency = now - vadStartTimeRef.current;
                addLog(`[Server] Speech start detected (${vadToServerLatency}ms after frontend VAD)`, 'latency');
              } else {
                vadStartTimeRef.current = now;
                addLog('[Server] Speech start detected (using as VAD start point)', 'latency');
              }
              break;

            case 'llm_start':
              llmStartTimeRef.current = now;
              if (vadEndTimeRef.current) {
                const browserVadLatency = now - vadEndTimeRef.current;
                const serverVadLatency = now - (speechEndTimeRef.current || vadEndTimeRef.current);
                addLog(`Transcribe latency - Browser VAD: ${browserVadLatency}ms`, 'latency');
                addLog(`Transcribe latency - Server VAD: ${serverVadLatency}ms`, 'latency');
              }
              break;

            case 'llm_first_token':
              if (llmStartTimeRef.current) {
                const latency = now - llmStartTimeRef.current;
                addLog(`LLM time to first token: ${latency}ms`, 'latency');
              }
              break;

            case 'llm_first_sentence':
              if (vadEndTimeRef.current) {
                const llmLatency = now - llmStartTimeRef.current;
                const browserVadLatency = now - vadEndTimeRef.current;
                const serverVadLatency = now - (speechEndTimeRef.current || vadEndTimeRef.current);
                addLog(`LLM first sentence latency - LLM: ${llmLatency}ms`, 'latency');
                addLog(`LLM first sentence latency - Browser VAD: ${browserVadLatency}ms`, 'latency');
                addLog(`LLM first sentence latency - Server VAD: ${serverVadLatency}ms`, 'latency');
              }
              break;

            case 'tts_complete':
              if (vadEndTimeRef.current) {
                addLog(`TTS synthesis time: ${jsonData.synthesisTime}ms`, 'latency');
              }
              break;

            case 'audio_start':
              // Reset playback start time when new audio stream starts
              playbackStartTimeRef.current = null;
              if (echoNodeRef.current) {
                echoNodeRef.current.port.postMessage({ type: 'unmute' });
              }
              addLog(`Audio format: ${JSON.stringify(jsonData.format)}`);
              audioFormatRef.current = jsonData.format;
              break;
            
            case 'audio_end':
              addLog('Audio streaming completed');
              break;
            
            case 'transcript':
              if (jsonData.messageId) {
                // Update the current valid message ID when receiving a transcript
                currentValidMessageIdRef.current = jsonData.messageId;
              }
              if (jsonData.isFinal) {
                addLog(`[ASR] Final transcript: "${jsonData.text}"`);
              } else {
                addLog(`[ASR] Interim transcript: "${jsonData.text}"`);
              }
              break;
            
            case 'error':
              addLog(`Error: ${jsonData.message}`, 'error');
              break;
            
            case 'llm_sentence':
              if (jsonData.messageId === currentValidMessageIdRef.current) {
                addLog(`LLM: "${jsonData.text}"`, 'llm');
              } else {
                addLog(`Ignored LLM response for recalled message: "${jsonData.text}"`, 'info');
              }
              break;
            
            case 'websocket_latency':
              addLog(`WebSocket RTT: ${jsonData.roundTripTime}ms`, 'latency');
              break;

            case 'chat_history_delta':
              setChatHistory(prev => {
                // Remove messages from startIndex onwards and insert new messages
                return [
                  ...prev.slice(0, jsonData.startIndex),
                  ...jsonData.messages
                ];
              });
              break;
            
            case 'debug_info':
              addLog(jsonData.message, 'info');
              break;
            
            case 'vad_status':
              // Silently ignore VAD status messages to reduce log noise
              break;
            
            default:
              addLog(`Received message: ${JSON.stringify(jsonData)}`);
          }
        }
      } catch (error) {
        addLog(`Error processing message: ${error}`, 'error');
      }
    };

    websocketRef.current.onclose = () => {
      addLog('WebSocket closed');
      websocketRef.current = null;
      // A server restart or network blip fires onclose mid-session. Without
      // tearing down, the button stays "Stop Recording", the mic keeps
      // capturing, the ping interval keeps firing, and the audio worklet
      // silently discards every captured buffer (it checks
      // websocketRef.current?.readyState, now null) -- a "zombie recording".
      // websocketRef is already null here, so stopRecording won't re-close the
      // socket or re-enter onclose.
      stopRecording();
    };

    websocketRef.current.onerror = (error) => {
      addLog(`WebSocket error: ${error}`, 'error');
    };
  };

  const startRecording = async () => {
    try {
      // Setup WebSocket first
      setupWebSocket();
      
      // Check if AudioContext and AudioWorklet are supported
      if (!window.AudioContext && !(window as any).webkitAudioContext) {
        throw new Error('AudioContext is not supported in this browser');
      }

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      
      // Create AudioContext with specific sample rate
      audioContextRef.current = new AudioContextClass({
        sampleRate: 16000
      });
      
      // Check if audioWorklet is supported
      if (!audioContextRef.current.audioWorklet) {
        throw new Error('AudioWorklet is not supported in this browser. Please use a modern browser like Chrome or Firefox.');
      }
      
      // Resume the audio context first (needed for some browsers)
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }
      
      console.log('Audio context created with sample rate:', audioContextRef.current.sampleRate);
      
      try {
        // Add the audio worklet module with the full URL path
        const workletUrl = new URL('/audioWorklet.js', window.location.origin).href;
        console.log('Loading audio worklet from:', workletUrl);
        
        // Add a timeout to the worklet loading
        const workletLoadPromise = audioContextRef.current.audioWorklet.addModule(workletUrl);
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Audio worklet load timeout')), 5000);
        });
        
        await Promise.race([workletLoadPromise, timeoutPromise]);
        console.log('Audio worklet loaded successfully');
        
      } catch (workletError) {
        console.error('Error loading audio worklet:', workletError);
        throw new Error(`Failed to load audio worklet module: ${workletError.message}`);
      }

      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia is not supported in this browser');
      }

      // Get user media after worklet is loaded
      try {
        streamRef.current = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          } 
        });
      } catch (mediaError) {
        console.error('Error accessing microphone:', mediaError);
        throw new Error(`Microphone access failed: ${mediaError.message}`);
      }
      
      try {
        sourceNodeRef.current = audioContextRef.current.createMediaStreamSource(streamRef.current);
        workletNodeRef.current = new AudioWorkletNode(audioContextRef.current, 'audio-processor');
        echoNodeRef.current = new AudioWorkletNode(audioContextRef.current, 'echo-processor');
        
        sourceNodeRef.current.connect(workletNodeRef.current);
        echoNodeRef.current.connect(audioContextRef.current.destination);

        console.log('Audio nodes connected successfully');
      } catch (nodeError) {
        console.error('Error setting up audio nodes:', nodeError);
        throw new Error(`Audio node setup failed: ${nodeError.message}`);
      }

      workletNodeRef.current.port.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          if (websocketRef.current?.readyState === WebSocket.OPEN) {
            websocketRef.current.send(event.data);
          }
        } else if (event.data.type === 'vad') {
          if (event.data.status === 'speech_end') {
            vadEndTimeRef.current = Date.now();
            hasPlaybackLatencyRef.current = false;
            addLog('[Frontend VAD] End of speech detected');
          } else if (event.data.status === 'speech_start') {
            vadStartTimeRef.current = Date.now();
            addLog('[Frontend VAD] Start of speech detected');
          }
        }
      };

      // Add message handler for the echo node
      echoNodeRef.current.port.onmessage = (event) => {
        if (event.data.type === 'queue_empty' && isPlayingRef.current) {
          isPlayingRef.current = false;

          // Reset playback state
          playbackStartTimeRef.current = null;
          hasPlaybackLatencyRef.current = false;
          addLog('Audio playback completed');
        }
      };

      setIsRecording(true);
    } catch (error) {
      console.error('Error in startRecording:', error);
      addLog(`Error: ${error.message}`, 'error');
      // Clean up any partially initialized resources
      stopRecording();
    }
  };

  const stopRecording = () => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    hasPlaybackLatencyRef.current = false;
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
    }
    if (echoNodeRef.current) {
      echoNodeRef.current.disconnect();
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      // Guard against closing an already-closed context (stopRecording is now
      // idempotent because onclose also calls it).
      if (audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
      audioContextRef.current = null;
    }
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setIsRecording(false);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  // Add this helper function before the return statement
  const formatLatencyLog = (message: string) => {
    // Check if it's a latency message with ":" or "-"
    const splitChar = message.includes(':') ? ':' : message.includes('-') ? '-' : null;
    if (!splitChar) return message;

    const [label, values] = message.split(splitChar);
    return (
      <div className="grid grid-cols-[1fr,auto] gap-2">
        <span>{label}{splitChar}</span>
        <span className="font-mono">{values}</span>
      </div>
    );
  };

  // Update the handleInterrupt function
  const handleInterrupt = () => {
    // Stop current audio playback and clear queue
    if (echoNodeRef.current) {
      echoNodeRef.current.port.postMessage({ type: 'clear' });
      echoNodeRef.current.port.postMessage({ type: 'mute' });
      echoNodeRef.current.disconnect();
      echoNodeRef.current.connect(audioContextRef.current!.destination);
    }
    audioQueueRef.current = [];

    // Reset playback state
    playbackStartTimeRef.current = null;
    hasPlaybackLatencyRef.current = false;
    isPlayingRef.current = false;
  };

  // Add scroll event handlers
  const handleChatScroll = () => {
    if (!chatHistoryRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatHistoryRef.current;
    // Consider "at bottom" if within 100 pixels of the bottom
    shouldAutoScrollChatRef.current = scrollHeight - (scrollTop + clientHeight) < 100;
  };

  const handleLogsScroll = () => {
    if (!logsRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = logsRef.current;
    // Consider "at bottom" if within 100 pixels of the bottom
    shouldAutoScrollLogsRef.current = scrollHeight - (scrollTop + clientHeight) < 100;
  };

  // Add scroll to bottom functions
  const scrollChatToBottom = () => {
    if (chatHistoryRef.current && shouldAutoScrollChatRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  };

  const scrollLogsToBottom = () => {
    if (logsRef.current && shouldAutoScrollLogsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  };

  // Update useEffect to scroll when chat history or logs change
  useEffect(() => {
    scrollChatToBottom();
  }, [chatHistory]);

  useEffect(() => {
    scrollLogsToBottom();
  }, [logs]);

  // Tear down the mic stream, AudioContext, WebSocket and ping interval if the
  // component unmounts mid-recording (client-side nav / fast refresh), instead
  // of leaving the microphone active and the ping interval firing.
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);



  return (
    <div className="min-h-screen flex flex-col bg-gray-100 p-2 sm:p-4">
      {/* Top Controls */}
      <div className="mb-4 flex flex-col sm:flex-row justify-center gap-2 sm:gap-4">
        <Button
          onClick={isRecording ? stopRecording : startRecording}
          variant={isRecording ? "destructive" : "default"}
          className={`px-4 sm:px-8 py-4 sm:py-6 text-base sm:text-lg font-semibold flex items-center justify-center gap-2 ${
            !isRecording ? 'bg-green-600 hover:bg-green-700' : ''
          }`}
        >
          {isRecording ? (
            <>
              <MicOff className="w-5 h-5 sm:w-6 sm:h-6" />
              Stop Recording
            </>
          ) : (
            <>
              <Mic className="w-5 h-5 sm:w-6 sm:h-6" />
              Start Recording
            </>
          )}
        </Button>
        <Button
          onClick={clearLogs}
          variant="outline"
          className="px-4 sm:px-8 py-4 sm:py-6 text-base sm:text-lg font-semibold flex items-center justify-center gap-2"
        >
          <Trash2 className="w-5 h-5 sm:w-6 sm:h-6" />
          Clear Logs
        </Button>
      </div>

      {/* Mobile Tabs - Only show on small screens */}
      <div className="lg:hidden mb-2">
        <div className="flex border-b border-gray-200">
          <TabButton 
            active={activeTab === 'chat'} 
            onClick={() => setActiveTab('chat')}
          >
            Chat History
          </TabButton>
          <TabButton 
            active={activeTab === 'logs'} 
            onClick={() => setActiveTab('logs')}
          >
            Logs
          </TabButton>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-col lg:flex-row flex-1 gap-2 sm:gap-4">
        {/* Chat History Panel */}
        <div className={`w-full lg:w-1/2 h-[calc(100vh-12rem)] lg:h-[calc(90vh-5rem)] ${
          activeTab === 'chat' ? 'block' : 'hidden lg:block'
        }`}>
          <Card className="h-full">
            <CardHeader className="pb-2 hidden lg:block">
              <CardTitle className="text-center text-base sm:text-lg">Chat History</CardTitle>
            </CardHeader>
            <CardContent 
              ref={chatHistoryRef}
              onScroll={handleChatScroll}
              className="h-full lg:h-[calc(100%-3rem)] overflow-y-auto pt-4 lg:pt-0"
            >
              <div className="flex flex-col space-y-4">
                {chatHistory.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === 'assistant' ? 'bg-gray-50' : 
                      message.role === 'transcript' ? 'bg-blue-50' :
                      'bg-white'
                    } p-3 sm:p-4 rounded-lg animate-slide-in`}
                  >
                    <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full flex-shrink-0 mr-3 sm:mr-4">
                      {message.role === 'assistant' ? (
                        <div className="w-full h-full bg-green-600 rounded-full flex items-center justify-center text-white text-xs sm:text-sm">
                          AI
                        </div>
                      ) : message.role === 'transcript' ? (
                        <div className="w-full h-full bg-blue-600 rounded-full flex items-center justify-center text-white text-xs sm:text-sm">
                          T
                        </div>
                      ) : (
                        <div className="w-full h-full bg-gray-600 rounded-full flex items-center justify-center text-white text-xs sm:text-sm">
                          U
                        </div>
                      )}
                    </div>
                    <div className="flex-1 prose prose-sm dark:prose-invert prose-p:my-3 prose-headings:mb-3 prose-headings:mt-6 prose-li:my-2 prose-pre:bg-gray-800 prose-pre:text-gray-100 max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code: CodeBlock,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                      {message.role === 'transcript' && !message.isFinal && (
                        <span className="text-xs text-gray-500 ml-2 animate-fade-in">(typing...)</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Logs Panel */}
        <div className={`w-full lg:w-1/2 h-[calc(100vh-12rem)] lg:h-[calc(90vh-5rem)] ${
          activeTab === 'logs' ? 'block' : 'hidden lg:block'
        }`}>
          <Card className="h-full overflow-hidden">
            <CardHeader className="pb-2 hidden lg:block">
              <CardTitle className="text-center text-base sm:text-lg">Logs</CardTitle>
            </CardHeader>
            <CardContent 
              ref={logsRef}
              onScroll={handleLogsScroll}
              className="h-full lg:h-[calc(100%-3rem)] bg-gray-900 p-2 lg:p-3 overflow-y-auto"
            >
              <div className="font-mono text-xs sm:text-sm">
                {logs.map((log, index) => {
                  const time = new Date(log.timestamp).toISOString().split('T')[1].slice(0, -1);
                  const baseClasses = "mb-1 font-mono";
                  
                  const typeClasses = {
                    error: "text-red-400",
                    latency: "text-cyan-400",
                    llm: "text-green-400",
                    info: "text-gray-300"
                  };

                  // Special styling for different event types
                  const prefixColor = {
                    vad: "text-purple-400",
                    asr: "text-yellow-400",
                    server: "text-blue-400"
                  };

                  let content = log.message;
                  let prefix = null;

                  // Extract prefix if message starts with [Something]
                  const prefixMatch = log.message.match(/^\[(.*?)\]/);
                  if (prefixMatch) {
                    prefix = prefixMatch[0];
                    content = log.message.slice(prefix.length);
                  }

                  return (
                    <div key={index} className={`${baseClasses} ${typeClasses[log.type]}`}>
                      <span className="text-gray-500">[{time}]</span>{' '}
                      {prefix && (
                        <span className={
                          Object.entries(prefixColor).find(([key]) => 
                            prefix?.toLowerCase().includes(key))?.[1] || typeClasses[log.type]
                          }>
                          {prefix}
                        </span>
                      )}
                      {log.type === 'latency' ? (
                        formatLatencyLog(content)
                      ) : (
                        <span>{content}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

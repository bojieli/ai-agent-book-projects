import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AttentionStatsProps {
  attentionData: {
    tokens: string[];
    attention_matrix: number[][];
    num_layers: number;
    num_heads: number;
  };
}

export default function AttentionStats({ attentionData }: AttentionStatsProps) {
  // Calculate statistics from attention matrix
  const calculateStats = () => {
    const { attention_matrix, tokens } = attentionData;
    
    if (!attention_matrix || attention_matrix.length === 0) {
      return { avgAttention: [], maxAttention: [], entropy: [] };
    }

    const avgAttention = attention_matrix.map(row => {
      const sum = row.reduce((a, b) => a + b, 0);
      return sum / row.length;
    });

    const maxAttention = attention_matrix.map(row => Math.max(...row));

    // Calculate entropy for each position
    const entropy = attention_matrix.map(row => {
      const sum = row.reduce((a, b) => a + b, 0);
      if (sum === 0) return 0;
      
      const probs = row.map(v => v / sum);
      return -probs.reduce((e, p) => {
        if (p === 0) return e;
        return e + p * Math.log2(p);
      }, 0);
    });

    return { avgAttention, maxAttention, entropy };
  };

  const stats = calculateStats();
  
  // Prepare data for chart
  const chartData = attentionData.tokens.slice(0, stats.avgAttention.length).map((token, idx) => ({
    position: idx,
    token: token.length > 10 ? token.substring(0, 10) + '...' : token,
    avgAttention: stats.avgAttention[idx]?.toFixed(4) || 0,
    maxAttention: stats.maxAttention[idx]?.toFixed(4) || 0,
    entropy: stats.entropy[idx]?.toFixed(4) || 0,
  }));

  // Calculate global statistics
  const globalStats = {
    avgAttention: stats.avgAttention.reduce((a, b) => a + b, 0) / stats.avgAttention.length || 0,
    maxAttention: Math.max(...stats.maxAttention) || 0,
    avgEntropy: stats.entropy.reduce((a, b) => a + b, 0) / stats.entropy.length || 0,
  };

  return (
    <div className="space-y-4">
      <div className="card">
        <h3 className="section-title">Attention Statistics</h3>
        
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {globalStats.avgAttention.toFixed(4)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Avg Attention</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {globalStats.maxAttention.toFixed(4)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Max Attention</div>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {globalStats.avgEntropy.toFixed(4)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Avg Entropy</div>
          </div>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="position" 
                label={{ value: 'Token Position', position: 'insideBottom', offset: -5 }}
              />
              <YAxis label={{ value: 'Value', angle: -90, position: 'insideLeft' }} />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg">
                        <p className="font-medium mb-2">Token: {data.token}</p>
                        <p className="text-sm text-blue-600">Avg: {data.avgAttention}</p>
                        <p className="text-sm text-green-600">Max: {data.maxAttention}</p>
                        <p className="text-sm text-purple-600">Entropy: {data.entropy}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="avgAttention" 
                stroke="#3B82F6" 
                name="Average"
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="maxAttention" 
                stroke="#10B981" 
                name="Maximum"
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="entropy" 
                stroke="#8B5CF6" 
                name="Entropy"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 className="section-title">Model Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Number of Layers:</span>
            <span className="font-medium">{attentionData.num_layers}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Number of Heads:</span>
            <span className="font-medium">{attentionData.num_heads}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Sequence Length:</span>
            <span className="font-medium">{attentionData.tokens.length}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Matrix Dimension:</span>
            <span className="font-medium">{attentionData.attention_matrix.length} × {attentionData.attention_matrix[0]?.length || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

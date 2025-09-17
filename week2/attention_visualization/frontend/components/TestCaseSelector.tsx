import React from 'react';

interface TestCase {
  id: number;
  category: string;
  query: string;
  description: string;
}

interface TestCaseSelectorProps {
  testCases: TestCase[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}

export default function TestCaseSelector({ testCases, selectedIndex, onSelect }: TestCaseSelectorProps) {
  const categoryColors: { [key: string]: string } = {
    'Math': 'bg-blue-100 text-blue-800',
    'Knowledge': 'bg-green-100 text-green-800',
    'Reasoning': 'bg-purple-100 text-purple-800',
    'Code': 'bg-orange-100 text-orange-800',
    'Creative': 'bg-pink-100 text-pink-800',
    'Tool Use': 'bg-indigo-100 text-indigo-800',
    'Custom': 'bg-gray-100 text-gray-800'
  };

  return (
    <div className="card">
      <h3 className="section-title">Test Cases</h3>
      
      <div className="space-y-2">
        {testCases.map((testCase, index) => (
          <button
            key={testCase.id}
            onClick={() => onSelect(index)}
            className={`w-full text-left p-3 rounded-lg border transition-colors group ${
              selectedIndex === index 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-200 hover:border-primary-300 hover:bg-primary-50'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className={`text-xs px-2 py-1 rounded-full ${categoryColors[testCase.category] || 'bg-gray-100 text-gray-800'}`}>
                    {testCase.category}
                  </span>
                  {selectedIndex === index && (
                    <span className="text-xs text-primary-600">● Selected</span>
                  )}
                </div>
                <p className={`text-sm font-medium ${
                  selectedIndex === index ? 'text-primary-700' : 'text-gray-900 group-hover:text-primary-700'
                }`}>
                  {testCase.query.length > 60 ? testCase.query.substring(0, 60) + '...' : testCase.query}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {testCase.description}
                </p>
              </div>
              <svg className={`h-5 w-5 flex-shrink-0 ml-2 mt-1 transition-colors ${
                selectedIndex === index ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

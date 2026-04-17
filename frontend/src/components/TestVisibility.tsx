import React from 'react';

// Test component to verify text visibility issue
const TestVisibility: React.FC = () => {
  return (
    <div className="p-8">
      <h2 className="text-white mb-4">Test: White Background with Different Text Colors</h2>
      
      <div className="bg-white p-4 mb-4 rounded border">
        <p className="text-sm">Default text (should be dark)</p>
        <p className="text-sm text-gray-800">text-gray-800</p>
        <p className="text-sm text-black">text-black</p>
        <p className="text-sm !text-black">!text-black (important)</p>
        <p className="text-sm !text-gray-800">!text-gray-800 (important)</p>
      </div>
      
      <div className="bg-gray-50 p-4 mb-4 rounded border">
        <p className="text-sm">Default text in gray-50</p>
        <p className="text-sm text-gray-800">text-gray-800</p>
        <p className="text-sm text-black">text-black</p>
        <p className="text-sm !text-black">!text-black (important)</p>
      </div>
      
      <div className="p-4 bg-white border border-gray-300 rounded shadow-sm">
        <div className="flex justify-between items-start mb-2">
          <span className="font-bold !text-cyan-800">Factor Name</span>
          <span className="text-xs px-2 py-1 rounded bg-green-100 !text-green-800 border border-green-200">
            Positive
          </span>
        </div>
        <p className="text-sm !text-black mb-2">This is the explanation text that should be visible</p>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 border border-gray-300 bg-gray-100 rounded">
            <div className="h-full bg-yellow-500 rounded" style={{ width: '75%' }} />
          </div>
          <span className="text-xs !text-yellow-600 w-8 text-right">75%</span>
        </div>
      </div>
    </div>
  );
};

export default TestVisibility;
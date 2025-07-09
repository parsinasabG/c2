import React from 'react';
import './App.css'; // Assuming you might add more specific styles here later

function App() {
  return (
    <div className="App">
      <header className="bg-gray-800 text-white p-4 text-center">
        <h1 className="text-2xl">CMMS Application</h1>
      </header>
      <main className="p-4">
        <p className="text-lg">
          Welcome to the Computerized Maintenance Management System.
        </p>
        <div className="mt-4 p-6 max-w-sm mx-auto bg-white rounded-xl shadow-md flex items-center space-x-4">
          <div className="flex-shrink-0">
            {/* Placeholder for an icon or image */}
            <svg className="h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 16v-2m0-10v2m0 6v2m-6-2H4m16 0h-2m-10-2V4m6 0v2M4 12H2m10 10v2m0-10v-2m6 2h2m-2-6V4m-6 16v-2m8-10H4a2 2 0 00-2 2v8a2 2 0 002 2h16a2 2 0 002-2v-8a2 2 0 00-2-2z" />
            </svg>
          </div>
          <div>
            <div className="text-xl font-medium text-black">Asset Management</div>
            <p className="text-gray-500">Module coming soon!</p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

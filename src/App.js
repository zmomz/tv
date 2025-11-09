import React, { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [backendStatus, setBackendStatus] = useState('');

  useEffect(() => {
    setMessage('Hello from React!');

    // Make a call to the backend health check endpoint
    fetch('/health')
      .then(response => response.json())
      .then(data => setBackendStatus(data.status))
      .catch(error => {
        console.error('Error fetching backend status:', error);
        setBackendStatus('Backend unreachable');
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>{message}</p>
        <p>Backend Status: {backendStatus}</p>
      </header>
    </div>
  );
}

export default App;

import React, { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [backendStatus, setBackendStatus] = useState('');
  const [positionGroups, setPositionGroups] = useState([]);

  useEffect(() => {
    setMessage('Hello from React!');

    // Fetch backend status
    fetch('/api/health')
      .then(response => response.json())
      .then(data => setBackendStatus(data.status))
      .catch(error => {
        console.error('Error fetching backend status:', error);
        setBackendStatus('Backend unreachable');
      });

    // Fetch position groups
    fetch('/api/position_groups')
      .then(response => response.json())
      .then(data => setPositionGroups(data))
      .catch(error => {
        console.error('Error fetching position groups:', error);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>{message}</p>
        <p>Backend Status: {backendStatus}</p>
      </header>
      <main>
        <h2>Position Groups</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Pair</th>
              <th>Status</th>
              <th>Unrealized PnL (%)</th>
            </tr>
          </thead>
          <tbody>
            {positionGroups.map(group => (
              <tr key={group.id}>
                <td>{group.id}</td>
                <td>{group.pair}</td>
                <td>{group.status}</td>
                <td>{group.unrealized_pnl_percent}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </div>
  );
}

export default App;

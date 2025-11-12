import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { api } from '../../services/api';

const Dashboard = ({ health }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/dashboard/stats');
        setStats(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">Error: {error.message}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Live Dashboard
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'space-around', mt: 3 }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6">Open Positions</Typography>
          <Typography variant="h3">{stats.open_positions}</Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6">Total Positions</Typography>
          <Typography variant="h3">{stats.total_positions}</Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6">PnL</Typography>
          <Typography variant="h3">{stats.pnl}</Typography>
        </Box>
      </Box>
      {/* Health Status */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>System Health</Typography>
        <Typography>Database: {health?.database}</Typography>
        <Typography>Redis: {health?.redis}</Typography>
        <Typography>Backend Status: {health?.status}</Typography>
      </Box>
    </Box>
  );
};

export default Dashboard;
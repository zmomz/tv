import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Grid,
  Paper,
} from '@mui/material';
import { api } from '../../services/api';

const PerformancePage = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await api.get('/analytics');
        setAnalytics(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading performance data...</Typography>
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
        Performance Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Total PnL</Typography>
            <Typography variant="h3" color={analytics.total_pnl >= 0 ? 'success.main' : 'error.main'}>
              {analytics.total_pnl?.toFixed(2) || 'N/A'}
            </Typography>
          </Paper>
        </Grid>
        <Grid xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Total ROI</Typography>
            <Typography variant="h3" color={analytics.total_roi >= 0 ? 'success.main' : 'error.main'}>
              {analytics.total_roi?.toFixed(2) || 'N/A'}%
            </Typography>
          </Paper>
        </Grid>
        <Grid xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Win Rate</Typography>
            <Typography variant="h3">
              {analytics.win_rate?.toFixed(2) || 'N/A'}%
            </Typography>
          </Paper>
        </Grid>
        <Grid xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Equity Curve</Typography>
            {/* Placeholder for a chart component */}
            <Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.200' }}>
              <Typography variant="body2" color="text.secondary">Equity Curve Chart Placeholder</Typography>
            </Box>
          </Paper>
        </Grid>
        <Grid xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Key Stats</Typography>
            <Typography>Total Trades: {analytics.total_trades || 'N/A'}</Typography>
            <Typography>Winning Trades: {analytics.winning_trades || 'N/A'}</Typography>
            <Typography>Losing Trades: {analytics.losing_trades || 'N/A'}</Typography>
            <Typography>Max Drawdown: {analytics.max_drawdown?.toFixed(2) || 'N/A'}%</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PerformancePage;

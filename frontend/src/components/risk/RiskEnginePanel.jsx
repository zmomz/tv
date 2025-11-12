import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert, Paper, Grid } from '@mui/material';
import { api } from '../../services/api';

const RiskEnginePanel = () => {
  const [riskStats, setRiskStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRiskStats = async () => {
      try {
        const response = await api.get('/risk-engine/stats');
        setRiskStats(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRiskStats();
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
        Risk Engine Panel
      </Typography>
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} md={6} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Current Status</Typography>
            <Typography>Loss %: {riskStats.loss_percent}</Typography>
            <Typography>Loss USD: {riskStats.loss_usd}</Typography>
            <Typography>Timer Remaining: {riskStats.timer_remaining}</Typography>
            <Typography>5 Pyramids Reached: {riskStats.five_pyramids_reached ? 'Yes' : 'No'}</Typography>
            <Typography>Age Filter Passed: {riskStats.age_filter_passed ? 'Yes' : 'No'}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Offset Opportunities</Typography>
            <Typography>Available Winning Offsets: {riskStats.available_winning_offsets}</Typography>
            <Typography>Total Winning Profit USD: {riskStats.total_winning_profit_usd}</Typography>
            <Typography>Projected Plan: {riskStats.projected_plan}</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RiskEnginePanel;

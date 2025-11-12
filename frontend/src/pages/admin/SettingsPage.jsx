import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Container,
  FormControlLabel,
  Grid,
  Paper,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { api } from '../../services/api';

const SettingsPage = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await api.get('/config');
        setConfig(response.data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    const [section, key] = name.split('.');

    let newValue = value;
    if (type === 'number') {
      newValue = value === '' ? '' : parseFloat(value);
    } else if (type === 'checkbox') {
      newValue = checked;
    }

    setConfig((prevConfig) => ({
      ...prevConfig,
      [section]: {
        ...prevConfig[section],
        [key]: newValue,
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccess(false);
    setError(null);
    try {
      await api.put('/config', config);
      setSuccess(true);
    } catch (error) {
      setError(error.message);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !config) {
    return <Alert severity="error">Failed to load settings: {error}</Alert>;
  }

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        Engine Settings
      </Typography>
      {config && (
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <Grid container spacing={3}>
            {/* App Settings */}
            <Grid xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>App</Typography>
                <Grid container spacing={2}>
                  <Grid xs={12} sm={4}>
                    <TextField fullWidth label="Mode" name="app.mode" value={config.app.mode} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12} sm={4}>
                    <TextField fullWidth label="Data Directory" name="app.data_dir" value={config.app.data_dir} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12} sm={4}>
                    <TextField fullWidth label="Log Level" name="app.log_level" value={config.app.log_level} onChange={handleInputChange} />
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Exchange Settings */}
            <Grid xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Exchange</Typography>
                <Grid container spacing={2}>
                  <Grid xs={12} sm={6}>
                    <TextField fullWidth label="Name" name="exchange.name" value={config.exchange.name} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12} sm={6}>
                    <TextField fullWidth label="API Key" name="exchange.api_key" value={config.exchange.api_key} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12} sm={6}>
                    <TextField fullWidth type="password" label="API Secret" name="exchange.api_secret" value={config.exchange.api_secret} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12} sm={6}>
                    <TextField fullWidth type="number" label="Precision Refresh (sec)" name="exchange.precision_refresh_sec" value={config.exchange.precision_refresh_sec} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12}>
                    <FormControlLabel control={<Checkbox name="exchange.testnet" checked={config.exchange.testnet} onChange={handleInputChange} />} label="Testnet" />
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Execution Pool */}
            <Grid xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Execution Pool</Typography>
                <TextField fullWidth type="number" label="Max Open Groups" name="execution_pool.max_open_groups" value={config.execution_pool.max_open_groups} onChange={handleInputChange} sx={{ mb: 2 }} />
                <FormControlLabel control={<Checkbox name="execution_pool.count_pyramids" checked={config.execution_pool.count_pyramids} onChange={handleInputChange} />} label="Count Pyramids Towards Pool" />
              </Paper>
            </Grid>

            {/* Grid Strategy */}
            <Grid xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Grid Strategy</Typography>
                <TextField fullWidth type="number" label="Max Pyramids Per Group" name="grid_strategy.max_pyramids_per_group" value={config.grid_strategy.max_pyramids_per_group} onChange={handleInputChange} sx={{ mb: 2 }} />
                <TextField fullWidth type="number" label="Max DCA Per Pyramid" name="grid_strategy.max_dca_per_pyramid" value={config.grid_strategy.max_dca_per_pyramid} onChange={handleInputChange} sx={{ mb: 2 }} />
                <TextField fullWidth label="Take Profit Mode" name="grid_strategy.tp_mode" value={config.grid_strategy.tp_mode} onChange={handleInputChange} />
              </Paper>
            </Grid>

            {/* Risk Engine */}
            <Grid xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Risk Engine</Typography>
                <Grid container spacing={2}>
                  <Grid xs={12} sm={6}>
                    <TextField fullWidth type="number" label="Loss Threshold (%)" name="risk_engine.loss_threshold_percent" value={config.risk_engine.loss_threshold_percent} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12} sm={6}>
                    <TextField fullWidth type="number" label="Post Full Wait (min)" name="risk_engine.post_full_wait_minutes" value={config.risk_engine.post_full_wait_minutes} onChange={handleInputChange} />
                  </Grid>
                  <Grid xs={12}>
                    <FormControlLabel control={<Checkbox name="risk_engine.require_full_pyramids" checked={config.risk_engine.require_full_pyramids} onChange={handleInputChange} />} label="Require Full Pyramids for Activation" />
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>

          {success && <Alert severity="success" sx={{ mt: 2 }}>Settings saved successfully!</Alert>}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3, mb: 2 }}>
            Save Settings
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default SettingsPage;

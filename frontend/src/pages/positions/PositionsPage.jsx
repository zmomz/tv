import React, { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress, Alert } from '@mui/material';
import PositionRow from '../../components/positions/PositionRow';
import { api } from '../../services/api';

const PositionsPage = () => {
  const [positions, setPositions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const response = await api.get('/positions');
        setPositions(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPositions();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading positions...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Alert severity="error">Error: {error}</Alert>
      </Box>
    );
  }

  if (positions.length === 0) {
    return (
      <Box sx={{ mt: 4, p: 3 }}>
        <Typography variant="h6">No positions to display.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Positions & Pyramids
      </Typography>
      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table sx={{ minWidth: 650 }} aria-label="positions table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Status</TableCell>
              <TableCell align="right">Entry Price</TableCell>
              <TableCell align="right">Current Price</TableCell>
              <TableCell align="right">PnL</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions.map((position) => (
              <PositionRow key={position.id} row={position} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default PositionsPage;

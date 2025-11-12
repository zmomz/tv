import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { api } from '../../services/api';

const WaitingQueueView = () => {
  const [queueEntries, setQueueEntries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQueueEntries = async () => {
      try {
        const response = await api.get('/queue/entries');
        setQueueEntries(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchQueueEntries();
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

  if (queueEntries.length === 0) {
    return (
      <Box sx={{ mt: 4, p: 3 }}>
        <Typography variant="h6">No queued signals to display.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Waiting Queue
      </Typography>
      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table sx={{ minWidth: 650 }} aria-label="waiting queue table">
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell>Timeframe</TableCell>
              <TableCell align="right">Replacement Count</TableCell>
              <TableCell align="right">Expected Profit</TableCell>
              <TableCell align="right">Time in Queue</TableCell>
              <TableCell align="right">Priority Rank</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {queueEntries.map((entry) => (
              <TableRow
                key={entry.id}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell component="th" scope="row">
                  {entry.symbol}
                </TableCell>
                <TableCell>{entry.timeframe}</TableCell>
                <TableCell align="right">{entry.replacement_count}</TableCell>
                <TableCell align="right">{entry.expected_profit}</TableCell>
                <TableCell align="right">{entry.time_in_queue}</TableCell>
                <TableCell align="right">{entry.priority_rank}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default WaitingQueueView;

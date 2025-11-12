import React from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress } from '@mui/material';

const Positions = ({ positions }) => {
  if (!positions) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading...</Typography>
      </Box>
    );
  }

  if (positions.length === 0) {
    return (
      <Box sx={{ mt: 4 }}>
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
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Status</TableCell>
              <TableCell align="right">Entry Price</TableCell>
              <TableCell align="right">Current Price</TableCell>
              <TableCell align="right">PnL</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions.map((position) => (
              <TableRow
                key={position.id}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell component="th" scope="row">
                  {position.symbol}
                </TableCell>
                <TableCell align="right">{position.status}</TableCell>
                <TableCell align="right">{position.entry_price}</TableCell>
                <TableCell align="right">{position.current_price}</TableCell>
                <TableCell align="right">{position.pnl}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Positions;
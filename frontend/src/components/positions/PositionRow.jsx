import React, { useState } from 'react';
import {
  TableRow,
  TableCell,
  IconButton,
  Collapse,
  Box,
  Typography,
  Table,
  TableHead,
  TableBody,
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

const PositionRow = ({ row }) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {row.symbol}
        </TableCell>
        <TableCell align="right">{row.status}</TableCell>
        <TableCell align="right">{row.entry_price}</TableCell>
        <TableCell align="right">{row.current_price}</TableCell>
        <TableCell align="right">{row.pnl}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                DCA Legs
              </Typography>
              <Table size="small" aria-label="dca legs">
                <TableHead>
                  <TableRow>
                    <TableCell>Filled Price</TableCell>
                    <TableCell>Capital Weight</TableCell>
                    <TableCell align="right">TP Target</TableCell>
                    <TableCell align="right">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {row.dca_orders && row.dca_orders.map((dcaRow) => (
                    <TableRow key={dcaRow.id}>
                      <TableCell component="th" scope="row">
                        {dcaRow.filled_price}
                      </TableCell>
                      <TableCell>{dcaRow.capital_weight}</TableCell>
                      <TableCell align="right">{dcaRow.tp_target}</TableCell>
                      <TableCell align="right">{dcaRow.status}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

export default PositionRow;

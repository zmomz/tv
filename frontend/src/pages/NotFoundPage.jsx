import React from 'react';
import { Box, Typography } from '@mui/material';
import { Link } from 'react-router-dom';

const NotFoundPage = () => {
  return (
    <Box sx={{ textAlign: 'center', mt: 8 }}>
      <Typography variant="h1">404</Typography>
      <Typography variant="h4">Page Not Found</Typography>
      <Typography>
        The page you are looking for does not exist.
      </Typography>
      <Link to="/">Go to Dashboard</Link>
    </Box>
  );
};

export default NotFoundPage;

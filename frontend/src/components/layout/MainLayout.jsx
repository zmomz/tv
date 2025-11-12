import React, { useEffect, useState } from 'react';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ListAltIcon from '@mui/icons-material/ListAlt';
import SettingsIcon from '@mui/icons-material/Settings';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import { useAuth } from '../../hooks/useAuth';

const drawerWidth = 240;

const MainLayout = ({ children }) => {
  const { logout, user } = useAuth();
  const [menuItems, setMenuItems] = useState([
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Positions', icon: <ListAltIcon />, path: '/positions' },
    { text: 'Performance', icon: <AssessmentIcon />, path: '/performance' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ]);

  useEffect(() => {
    if (user && user.role === 'admin') {
      setMenuItems((prevItems) => [
        ...prevItems,
        { text: 'Logs', icon: <AssessmentIcon />, path: '/logs' },
      ]);
    }
  }, [user]);

  const handleLogout = () => {
    logout();
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap>
            Trading Engine
          </Typography>
        </Toolbar>
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem button component={Link} to={item.path} key={item.text}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
            <ListItem button onClick={handleLogout}>
              <ListItemIcon><ExitToAppIcon /></ListItemIcon>
              <ListItemText primary="Logout" />
            </ListItem>
          </List>
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default MainLayout;
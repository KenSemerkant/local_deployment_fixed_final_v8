import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, useTheme, IconButton, Menu, MenuItem } from '@mui/material';
import { AdminPanelSettings as AdminIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const [adminMenuAnchor, setAdminMenuAnchor] = React.useState<null | HTMLElement>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleAdminMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAdminMenuAnchor(event.currentTarget);
  };

  const handleAdminMenuClose = () => {
    setAdminMenuAnchor(null);
  };

  const handleAdminNavigation = (path: string) => {
    navigate(path);
    handleAdminMenuClose();
  };

  // Check if user is admin
  const isAdmin = (user as any)?.is_admin || false;

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ flexGrow: 1, cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          AI Financial Analyst
        </Typography>
        
        {isAuthenticated ? (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {isAdmin && (
              <>
                <IconButton
                  color="inherit"
                  onClick={handleAdminMenuOpen}
                  sx={{ mr: 1 }}
                >
                  <AdminIcon />
                </IconButton>
                <Menu
                  anchorEl={adminMenuAnchor}
                  open={Boolean(adminMenuAnchor)}
                  onClose={handleAdminMenuClose}
                >
                  <MenuItem onClick={() => handleAdminNavigation('/admin')}>
                    Admin Dashboard
                  </MenuItem>
                  <MenuItem onClick={() => handleAdminNavigation('/admin/users')}>
                    User Management
                  </MenuItem>
                  <MenuItem onClick={() => handleAdminNavigation('/admin/llm')}>
                    LLM Configuration
                  </MenuItem>
                  <MenuItem onClick={() => handleAdminNavigation('/admin/storage')}>
                    Storage Management
                  </MenuItem>
                  <MenuItem onClick={() => handleAdminNavigation('/admin/analytics')}>
                    Analytics
                  </MenuItem>
                </Menu>
              </>
            )}
            <Typography variant="body1" sx={{ mr: 2 }}>
              {user?.full_name || user?.email}
            </Typography>
            <Button color="inherit" onClick={handleLogout}>Logout</Button>
          </Box>
        ) : (
          <Box>
            <Button color="inherit" onClick={() => navigate('/login')}>Login</Button>
            <Button color="inherit" onClick={() => navigate('/register')}>Register</Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;

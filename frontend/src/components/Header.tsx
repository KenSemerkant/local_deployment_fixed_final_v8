import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, useTheme, IconButton, Menu, MenuItem, Avatar, Chip } from '@mui/material';
import { AdminPanelSettings as AdminIcon, DarkMode, LightMode } from '@mui/icons-material';
import { LogOut, User, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useColorMode } from '../contexts/ThemeContext';

const Header: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const { mode, toggleColorMode } = useColorMode();
  const [adminMenuAnchor, setAdminMenuAnchor] = React.useState<null | HTMLElement>(null);
  const [userMenuAnchor, setUserMenuAnchor] = React.useState<null | HTMLElement>(null);

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

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleAdminNavigation = (path: string) => {
    navigate(path);
    handleAdminMenuClose();
  };

  const handleUserNavigation = (path: string) => {
    navigate(path);
    handleUserMenuClose();
  };

  // Check if user is admin
  const isAdmin = (user as any)?.is_admin || false;

  return (
    <motion.div
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <AppBar
        position="static"
        sx={{
          background: theme.palette.background.paper,
          backdropFilter: 'blur(10px)',
          borderBottom: `1px solid ${theme.palette.divider}`,
          boxShadow: theme.shadows[1],
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{ flexGrow: 1 }}
          >
            <Typography
              variant="h5"
              component="div"
              sx={{
                flexGrow: 1,
                cursor: 'pointer',
                fontWeight: 700,
                color: theme.palette.text.primary,
                letterSpacing: '-0.025em',
              }}
              onClick={() => navigate('/')}
            >
              🤖 AI Financial Analyst
            </Typography>
          </motion.div>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <motion.div
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <IconButton
                onClick={toggleColorMode}
                color="inherit"
                sx={{
                  width: 40,
                  height: 40,
                  background: mode === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(10px)',
                  border: `1px solid ${theme.palette.divider}`,
                  '&:hover': {
                    background: mode === 'light' ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.2)',
                  }
                }}
              >
                {mode === 'dark' ? <LightMode /> : <DarkMode />}
              </IconButton>
            </motion.div>

            {isAuthenticated ? (
              <>
                {isAdmin && (
                  <motion.div
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <Chip
                      label="Admin"
                      sx={{
                        height: 40,
                        borderRadius: 20,
                        background: mode === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                        color: theme.palette.text.primary,
                        fontWeight: 600,
                        backdropFilter: 'blur(10px)',
                        border: `1px solid ${theme.palette.divider}`,
                        '& .MuiChip-icon': { color: 'inherit' }
                      }}
                      icon={<BarChart3 size={18} />}
                    />
                  </motion.div>
                )}

                {isAdmin && (
                  <>
                    <motion.div
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <IconButton
                        color="inherit"
                        onClick={handleAdminMenuOpen}
                        sx={{
                          width: 40,
                          height: 40,
                          background: mode === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                          backdropFilter: 'blur(10px)',
                          border: `1px solid ${theme.palette.divider}`,
                          '&:hover': {
                            background: mode === 'light' ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.2)',
                          }
                        }}
                      >
                        <AdminIcon />
                      </IconButton>
                    </motion.div>
                    <Menu
                      anchorEl={adminMenuAnchor}
                      open={Boolean(adminMenuAnchor)}
                      onClose={handleAdminMenuClose}
                      PaperProps={{
                        sx: {
                          background: mode === 'light' ? 'rgba(255, 255, 255, 0.95)' : 'rgba(30, 41, 59, 0.95)',
                          backdropFilter: 'blur(20px)',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          borderRadius: 2,
                          mt: 1,
                          minWidth: 200,
                        }
                      }}
                    >
                      <MenuItem
                        onClick={() => handleAdminNavigation('/admin')}
                        sx={{ borderRadius: 1, mx: 1, my: 0.5 }}
                      >
                        <BarChart3 size={18} style={{ marginRight: 8 }} />
                        Admin Dashboard
                      </MenuItem>
                      <MenuItem
                        onClick={() => handleAdminNavigation('/admin/users')}
                        sx={{ borderRadius: 1, mx: 1, my: 0.5 }}
                      >
                        <User size={18} style={{ marginRight: 8 }} />
                        User Management
                      </MenuItem>
                      <MenuItem
                        onClick={() => handleAdminNavigation('/admin/llm')}
                        sx={{ borderRadius: 1, mx: 1, my: 0.5 }}
                      >
                        🤖 LLM Configuration
                      </MenuItem>
                      <MenuItem
                        onClick={() => handleAdminNavigation('/admin/storage')}
                        sx={{ borderRadius: 1, mx: 1, my: 0.5 }}
                      >
                        💾 Storage Management
                      </MenuItem>
                      <MenuItem
                        onClick={() => handleAdminNavigation('/admin/analytics')}
                        sx={{ borderRadius: 1, mx: 1, my: 0.5 }}
                      >
                        📊 Analytics
                      </MenuItem>
                    </Menu>
                  </>
                )}

                {/* User Profile Dropdown */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <IconButton
                      onClick={handleUserMenuOpen}
                      sx={{
                        p: 0.5,
                        background: mode === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                        backdropFilter: 'blur(10px)',
                        border: `1px solid ${theme.palette.divider}`,
                        '&:hover': {
                          background: mode === 'light' ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.2)',
                        }
                      }}
                    >
                      <Avatar
                        src={user?.avatar_url ? (user.avatar_url.startsWith('http') ? user.avatar_url : `${process.env.REACT_APP_API_URL}${user.avatar_url}`) : undefined}
                        sx={{
                          width: 32,
                          height: 32,
                          fontSize: '0.875rem',
                          fontWeight: 600,
                        }}
                      >
                        {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                      </Avatar>
                    </IconButton>
                  </motion.div>

                  <Menu
                    anchorEl={userMenuAnchor}
                    open={Boolean(userMenuAnchor)}
                    onClose={handleUserMenuClose}
                    PaperProps={{
                      sx: {
                        background: mode === 'light' ? 'rgba(255, 255, 255, 0.95)' : 'rgba(30, 41, 59, 0.95)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                        mt: 1,
                        minWidth: 200,
                      }
                    }}
                  >
                    <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                      <Typography variant="subtitle2" noWrap sx={{ fontWeight: 600 }}>
                        {user?.full_name || 'User'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {user?.email}
                      </Typography>
                    </Box>

                    <MenuItem
                      onClick={() => handleUserNavigation('/profile')}
                      sx={{ borderRadius: 1, mx: 1, mt: 1 }}
                    >
                      <User size={18} style={{ marginRight: 8 }} />
                      Profile Settings
                    </MenuItem>

                    <MenuItem
                      onClick={handleLogout}
                      sx={{ borderRadius: 1, mx: 1, mb: 0.5, color: 'error.main' }}
                    >
                      <LogOut size={18} style={{ marginRight: 8 }} />
                      Logout
                    </MenuItem>
                  </Menu>
                </Box>
              </>
            ) : (
              <Box sx={{ display: 'flex', gap: 1 }}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    color="inherit"
                    onClick={() => navigate('/login')}
                    sx={{
                      background: mode === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(10px)',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 2,
                      px: 3,
                      py: 1,
                      fontWeight: 600,
                      '&:hover': {
                        background: mode === 'light' ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.2)',
                      }
                    }}
                  >
                    Login
                  </Button>
                </motion.div>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    color="inherit"
                    onClick={() => navigate('/register')}
                    sx={{
                      background: mode === 'light' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.2)',
                      backdropFilter: 'blur(10px)',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 2,
                      px: 3,
                      py: 1,
                      fontWeight: 600,
                      '&:hover': {
                        background: mode === 'light' ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.3)',
                      }
                    }}
                  >
                    Register
                  </Button>
                </motion.div>
              </Box>
            )}
          </Box>
        </Toolbar>
      </AppBar>
    </motion.div>
  );
};

export default Header;

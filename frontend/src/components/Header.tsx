import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, useTheme, IconButton, Menu, MenuItem, Avatar, Chip } from '@mui/material';
import { AdminPanelSettings as AdminIcon } from '@mui/icons-material';
import { LogOut, User, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';
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
    <motion.div
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <AppBar
        position="static"
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
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
                background: 'linear-gradient(45deg, #ffffff 30%, #f0f8ff 90%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '-0.025em',
              }}
              onClick={() => navigate('/')}
            >
              🤖 AI Financial Analyst
            </Typography>
          </motion.div>

          {isAuthenticated ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {isAdmin && (
                <motion.div
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <Chip
                    label="Admin"
                    size="small"
                    sx={{
                      background: 'rgba(255, 255, 255, 0.2)',
                      color: 'white',
                      fontWeight: 600,
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                    }}
                    icon={<BarChart3 size={16} />}
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
                        background: 'rgba(255, 255, 255, 0.1)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        '&:hover': {
                          background: 'rgba(255, 255, 255, 0.2)',
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
                        background: 'rgba(255, 255, 255, 0.95)',
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

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    background: 'rgba(255, 255, 255, 0.2)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                  }}
                >
                  {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                </Avatar>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontWeight: 500,
                    display: { xs: 'none', sm: 'block' }
                  }}
                >
                  {user?.full_name || user?.email}
                </Typography>
              </Box>

              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  color="inherit"
                  onClick={handleLogout}
                  startIcon={<LogOut size={18} />}
                  sx={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 2,
                    px: 2,
                    py: 1,
                    fontWeight: 600,
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.2)',
                    }
                  }}
                >
                  Logout
                </Button>
              </motion.div>
            </Box>
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
                    background: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 2,
                    px: 3,
                    py: 1,
                    fontWeight: 600,
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.2)',
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
                    background: 'rgba(255, 255, 255, 0.2)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    borderRadius: 2,
                    px: 3,
                    py: 1,
                    fontWeight: 600,
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.3)',
                    }
                  }}
                >
                  Register
                </Button>
              </motion.div>
            </Box>
          )}
        </Toolbar>
      </AppBar>
    </motion.div>
  );
};

export default Header;

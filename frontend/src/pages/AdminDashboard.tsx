import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  People as PeopleIcon,
  Settings as SettingsIcon,
  Storage as StorageIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  AdminPanelSettings as AdminIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();

  const adminCards = [
    {
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: <PeopleIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      action: () => navigate('/admin/users'),
      color: '#1976d2'
    },
    {
      title: 'LLM Configuration',
      description: 'Configure AI models and providers',
      icon: <SettingsIcon sx={{ fontSize: 40, color: 'secondary.main' }} />,
      action: () => navigate('/admin/llm'),
      color: '#9c27b0'
    },
    {
      title: 'Storage Management',
      description: 'Monitor and manage file storage, user data, and cleanup operations',
      icon: <StorageIcon sx={{ fontSize: 40, color: 'success.main' }} />,
      action: () => navigate('/admin/storage'),
      color: '#2e7d32'
    },
    {
      title: 'Analytics',
      description: 'View system analytics and reports',
      icon: <AnalyticsIcon sx={{ fontSize: 40, color: 'warning.main' }} />,
      action: () => navigate('/admin/analytics'),
      color: '#ed6c02'
    }
  ];

  const quickActions = [
    { text: 'Add New User', icon: <PeopleIcon />, action: () => navigate('/admin/users/new') },
    { text: 'System Health Check', icon: <SecurityIcon />, action: () => navigate('/admin/health') },
    { text: 'Clear Cache', icon: <StorageIcon />, action: () => console.log('Clear cache') },
    { text: 'Export Data', icon: <AnalyticsIcon />, action: () => console.log('Export data') }
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <AdminIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          Admin Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Manage your AI Financial Analyst application
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Main Admin Cards */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={3}>
            {adminCards.map((card, index) => (
              <Grid item xs={12} sm={6} key={index}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4
                    }
                  }}
                  onClick={card.action}
                >
                  <CardContent sx={{ flexGrow: 1, textAlign: 'center', pt: 3 }}>
                    <Box sx={{ mb: 2 }}>
                      {card.icon}
                    </Box>
                    <Typography variant="h6" component="h2" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {card.description}
                    </Typography>
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                    <Button 
                      size="small" 
                      variant="contained"
                      sx={{ backgroundColor: card.color }}
                    >
                      Manage
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>

        {/* Quick Actions Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              {quickActions.map((action, index) => (
                <ListItem 
                  key={index}
                  button
                  onClick={action.action}
                  sx={{
                    borderRadius: 1,
                    mb: 1,
                    '&:hover': {
                      backgroundColor: 'action.hover'
                    }
                  }}
                >
                  <ListItemIcon>
                    {action.icon}
                  </ListItemIcon>
                  <ListItemText primary={action.text} />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* System Status */}
          <Paper sx={{ p: 2, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Database</Typography>
              <Typography variant="body2" color="success.main">Healthy</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">LLM Service</Typography>
              <Typography variant="body2" color="success.main">Connected</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Storage</Typography>
              <Typography variant="body2" color="success.main">Available</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2">Cache</Typography>
              <Typography variant="body2" color="warning.main">75% Full</Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AdminDashboard;

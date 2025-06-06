import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Box, CircularProgress, Alert } from '@mui/material';

interface AdminRouteProps {
  children: React.ReactNode;
}

const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="50vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check if user has admin privileges
  // Note: This assumes the user object has an is_admin field
  // You may need to adjust this based on your actual user object structure
  const isAdmin = (user as any)?.is_admin || false;

  if (!isAdmin) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Access Denied: Admin privileges required to access this page.
        </Alert>
      </Box>
    );
  }

  return <>{children}</>;
};

export default AdminRoute;

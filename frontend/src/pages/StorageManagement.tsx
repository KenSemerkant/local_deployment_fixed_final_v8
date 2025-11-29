import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Snackbar,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Storage as StorageIcon,
  Delete as DeleteIcon,
  CleaningServices as CleanIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Description as FileIcon
} from '@mui/icons-material';
import api from '../services/api';

// Interfaces matching backend response
interface StorageOverview {
  total_size_bytes: number;
  used_size_bytes: number;
  free_size_bytes: number;
  total_files: number;
  file_types: Record<string, number>;
  minio_stats: {
    size_bytes: number;
    file_count: number;
  };
}

interface StoredFile {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

interface UserStorage {
  user_id: number;
  total_size_bytes: number;
  file_count: number;
  files: StoredFile[];
}

interface CleanupResult {
  cleaned_files_count: number;
  freed_size_bytes: number;
  message: string;
}

const StorageManagement: React.FC = () => {
  const [overview, setOverview] = useState<StorageOverview | null>(null);
  const [userStorage, setUserStorage] = useState<UserStorage[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [cleanupDialog, setCleanupDialog] = useState({
    open: false,
    type: '',
    userId: null as number | null,
    userEmail: ''
  });

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info' | 'warning'
  });

  useEffect(() => {
    loadStorageData();
  }, []);

  const loadStorageData = async () => {
    try {
      setLoading(true);

      // Sync metadata first
      await api.post('/admin/storage/sync');

      const [overviewResponse, userStorageResponse] = await Promise.all([
        api.get('/admin/storage/overview'),
        api.get('/admin/storage/users')
      ]);

      setOverview(overviewResponse.data);
      setUserStorage(userStorageResponse.data.users);

    } catch (error: any) {
      console.error('Error loading storage data:', error);
      showSnackbar('Error loading storage data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadStorageData();
    setRefreshing(false);
    showSnackbar('Storage data refreshed', 'success');
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const openCleanupDialog = (type: string, userId?: number, userEmail?: string) => {
    setCleanupDialog({
      open: true,
      type,
      userId: userId || null,
      userEmail: userEmail || ''
    });
  };

  const closeCleanupDialog = () => {
    setCleanupDialog({
      open: false,
      type: '',
      userId: null,
      userEmail: ''
    });
  };

  const performCleanup = async () => {
    try {
      let response;

      if (cleanupDialog.type === 'user' && cleanupDialog.userId) {
        response = await api.post(`/admin/storage/cleanup/user/${cleanupDialog.userId}`);
      } else if (cleanupDialog.type === 'orphaned') {
        response = await api.post('/admin/storage/cleanup/orphaned');
      } else {
        throw new Error('Invalid cleanup type');
      }

      const result: CleanupResult = response.data;

      showSnackbar(result.message, 'success');
      await loadStorageData();

    } catch (error: any) {
      console.error('Error performing cleanup:', error);
      showSnackbar('Error performing cleanup', 'error');
    } finally {
      closeCleanupDialog();
    }
  };

  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            Storage Management
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Monitor and manage system storage and cleanup operations
          </Typography>
        </Box>
        <Button
          variant="outlined"
          onClick={refreshData}
          disabled={refreshing}
          startIcon={refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Box>

      {/* Storage Overview */}
      {overview && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            System Storage Overview
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Used
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatBytes(overview.used_size_bytes)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Free Space
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatBytes(overview.free_size_bytes)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Files
                  </Typography>
                  <Typography variant="h4" component="div">
                    {overview.total_files.toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    MinIO Usage
                  </Typography>
                  <Typography variant="h4" component="div">
                    {formatBytes(overview.minio_stats.size_bytes)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {overview.minio_stats.file_count} objects
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
            File Types Distribution
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(overview.file_types).map(([type, count]) => (
              <Grid item key={type}>
                <Paper variant="outlined" sx={{ p: 1, px: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FileIcon color="action" fontSize="small" />
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {type || 'Unknown'}:
                  </Typography>
                  <Typography variant="body2">
                    {count}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* User Storage Details */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            User Storage Details
          </Typography>
          <Button
            variant="outlined"
            color="warning"
            onClick={() => openCleanupDialog('orphaned')}
            startIcon={<CleanIcon />}
          >
            Clean Orphaned Files
          </Button>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>User ID</TableCell>
                <TableCell align="right">Total Size</TableCell>
                <TableCell align="right">File Count</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {userStorage.map((user) => (
                <TableRow key={user.user_id}>
                  <TableCell>User {user.user_id}</TableCell>
                  <TableCell align="right">{formatBytes(user.total_size_bytes)}</TableCell>
                  <TableCell align="right">{user.file_count}</TableCell>
                  <TableCell align="center">
                    <Tooltip title="Clean up all user data">
                      <IconButton
                        color="error"
                        onClick={() => openCleanupDialog('user', user.user_id, `User ${user.user_id}`)}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {userStorage.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    No user storage data found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Cleanup Confirmation Dialog */}
      <Dialog open={cleanupDialog.open} onClose={closeCleanupDialog}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon color="warning" />
            Confirm Cleanup Operation
          </Box>
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {cleanupDialog.type === 'user' ? (
              <>
                Are you sure you want to clean up all storage data for <strong>{cleanupDialog.userEmail}</strong>?
                <br /><br />
                This will permanently delete all files associated with this user.
                <br />
                <strong>This action cannot be undone!</strong>
              </>
            ) : (
              <>
                Are you sure you want to clean up orphaned files?
                <br /><br />
                This will delete temporary files and cache entries that are no longer associated with any user or document.
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeCleanupDialog}>Cancel</Button>
          <Button onClick={performCleanup} color="error" variant="contained">
            Confirm Cleanup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default StorageManagement;

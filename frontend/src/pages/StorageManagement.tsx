import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Storage as StorageIcon,
  Folder as FolderIcon,
  Delete as DeleteIcon,
  CleaningServices as CleanIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import axios from 'axios';

interface StorageDirectory {
  path: string;
  size_bytes: number;
  size_formatted: string;
  file_count: number;
  exists: boolean;
  error?: string;
}

interface StorageOverview {
  total_size: number;
  total_size_formatted: string;
  total_files: number;
  directories: Record<string, StorageDirectory>;
  last_updated: string;
  error?: string;
}

interface UserStorage {
  user_id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at?: string;
  storage: {
    documents: {
      count: number;
      total_size: number;
      total_size_formatted: string;
    };
    cache: {
      count: number;
      total_size: number;
      total_size_formatted: string;
    };
    vector_db: {
      count: number;
      total_size: number;
      total_size_formatted: string;
    };
    analysis_results: number;
    qa_sessions: number;
    questions: number;
  };
}

interface CleanupResult {
  success: boolean;
  cleaned: Record<string, number>;
  errors: string[];
  error?: string;
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

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadStorageData();
  }, []);

  const loadStorageData = async () => {
    try {
      setLoading(true);
      
      // Load storage overview and user storage in parallel
      const [overviewResponse, userStorageResponse] = await Promise.all([
        axios.get(`${API_URL}/admin/storage/overview`),
        axios.get(`${API_URL}/admin/storage/users`)
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
        response = await axios.post(`${API_URL}/admin/storage/cleanup/user/${cleanupDialog.userId}`);
      } else if (cleanupDialog.type === 'orphaned') {
        response = await axios.post(`${API_URL}/admin/storage/cleanup/orphaned`);
      } else {
        throw new Error('Invalid cleanup type');
      }
      
      const result: CleanupResult = response.data;
      
      if (result.success) {
        const cleanedItems = Object.values(result.cleaned).reduce((sum, count) => sum + count, 0);
        showSnackbar(`Cleanup completed! Cleaned ${cleanedItems} items.`, 'success');
        
        // Refresh data
        await loadStorageData();
      } else {
        showSnackbar(`Cleanup failed: ${result.error}`, 'error');
      }
      
    } catch (error: any) {
      console.error('Error performing cleanup:', error);
      showSnackbar('Error performing cleanup', 'error');
    } finally {
      closeCleanupDialog();
    }
  };

  const getStorageUsageColor = (sizeBytes: number): string => {
    if (sizeBytes > 1024 * 1024 * 1024) return '#f44336'; // Red for > 1GB
    if (sizeBytes > 100 * 1024 * 1024) return '#ff9800'; // Orange for > 100MB
    if (sizeBytes > 10 * 1024 * 1024) return '#2196f3'; // Blue for > 10MB
    return '#4caf50'; // Green for < 10MB
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
            Monitor and manage system storage, user data, and cleanup operations
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
            Storage Overview
          </Typography>
          
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Storage Used
                  </Typography>
                  <Typography variant="h4" component="div">
                    {overview.total_size_formatted}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
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
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Last Updated
                  </Typography>
                  <Typography variant="h6" component="div">
                    {new Date(overview.last_updated).toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Directory Breakdown */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Storage Breakdown by Directory</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                {Object.entries(overview.directories).map(([name, dir]) => (
                  <ListItem key={name}>
                    <ListItemIcon>
                      <FolderIcon color={dir.exists ? 'primary' : 'disabled'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">{name.toUpperCase()}</Typography>
                          <Chip 
                            label={dir.size_formatted} 
                            size="small" 
                            sx={{ backgroundColor: getStorageUsageColor(dir.size_bytes), color: 'white' }}
                          />
                          <Chip label={`${dir.file_count} files`} size="small" variant="outlined" />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {dir.path}
                          </Typography>
                          {dir.error && (
                            <Typography variant="body2" color="error">
                              Error: {dir.error}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
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
                <TableCell>User</TableCell>
                <TableCell align="right">Documents</TableCell>
                <TableCell align="right">Cache</TableCell>
                <TableCell align="right">Vector DB</TableCell>
                <TableCell align="right">Analysis Results</TableCell>
                <TableCell align="right">Q&A Data</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {userStorage.map((user) => (
                <TableRow key={user.user_id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PersonIcon color={user.is_active ? 'primary' : 'disabled'} />
                      <Box>
                        <Typography variant="subtitle2">
                          {user.full_name || user.email}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {user.email}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <Typography variant="body2">
                        {user.storage.documents.total_size_formatted}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.storage.documents.count} files
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <Typography variant="body2">
                        {user.storage.cache.total_size_formatted}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.storage.cache.count} files
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <Typography variant="body2">
                        {user.storage.vector_db.total_size_formatted}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.storage.vector_db.count} DBs
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {user.storage.analysis_results}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <Typography variant="body2">
                        {user.storage.qa_sessions} sessions
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.storage.questions} questions
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Clean up all user data">
                      <IconButton
                        color="error"
                        onClick={() => openCleanupDialog('user', user.user_id, user.email)}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
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
                Are you sure you want to clean up all storage data for user <strong>{cleanupDialog.userEmail}</strong>?
                <br /><br />
                This will permanently delete:
                <ul>
                  <li>All uploaded documents</li>
                  <li>All cache files</li>
                  <li>All vector databases</li>
                  <li>All analysis results</li>
                  <li>All Q&A sessions and questions</li>
                </ul>
                <strong>This action cannot be undone!</strong>
              </>
            ) : (
              <>
                Are you sure you want to clean up orphaned files?
                <br /><br />
                This will delete temporary files and cache entries that are no longer associated with any user or document.
                This operation is generally safe but cannot be undone.
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

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Box, 
  Typography, 
  Button, 
  Paper, 
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Divider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  CloudUpload as CloudUploadIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { documentService, Document } from '../services/api';

const Dashboard: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);
  const [cancellingDocuments, setCancellingDocuments] = useState<Set<string>>(new Set());
  
  const { user } = useAuth();
  const navigate = useNavigate();

  console.log("Dashboard component mounted, user:", user);

  useEffect(() => {
    console.log("Dashboard useEffect triggered, fetching documents");
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    console.log("fetchDocuments called");
    setLoading(true);
    try {
      console.log("Calling documentService.getDocuments()");
      const docs = await documentService.getDocuments();
      console.log("Documents fetched successfully:", docs);
      
      // Debug: Check if docs is an array
      if (!Array.isArray(docs)) {
        console.error("Fetched documents is not an array:", docs);
        setError('Received invalid document data format. Please contact support.');
      } else {
        console.log(`Received ${docs.length} documents`);
        setDocuments(docs);
        setError('');
      }
    } catch (err: any) {
      console.error('Error fetching documents:', err);
      console.error('Error details:', err.response?.data);
      setError('Failed to load documents. Please try again.');
    } finally {
      console.log("Setting loading to false");
      setLoading(false);
    }
  };

  const handleUploadClick = () => {
    setUploadDialogOpen(true);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setUploading(true);
    try {
      await documentService.uploadDocument(selectedFile);
      setUploadDialogOpen(false);
      setSelectedFile(null);
      fetchDocuments();
    } catch (err: any) {
      console.error('Error uploading document:', err);
      setError('Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteClick = (documentId: string) => {
    setDocumentToDelete(documentId);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!documentToDelete) return;
    
    try {
      await documentService.deleteDocument(documentToDelete);
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
      fetchDocuments();
    } catch (err: any) {
      console.error('Error deleting document:', err);
      setError('Failed to delete document. Please try again.');
    }
  };

  const handleViewDocument = (documentId: string) => {
    navigate(`/documents/${documentId}`);
  };

  const handleCancelProcessing = async (documentId: string) => {
    setCancellingDocuments(prev => new Set(prev).add(documentId));
    try {
      await documentService.cancelProcessing(documentId);
      fetchDocuments(); // Refresh to show updated status
    } catch (err: any) {
      console.error('Error cancelling document processing:', err);
      setError('Failed to cancel document processing. Please try again.');
    } finally {
      setCancellingDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
      case 'PROCESSED':
        return 'success.main';
      case 'PROCESSING':
      case 'UPLOADED':
        return 'info.main';
      case 'ERROR':
        return 'error.main';
      case 'CANCELLED':
        return 'warning.main';
      default:
        return 'text.secondary';
    }
  };

  console.log("Dashboard rendering, loading:", loading, "documents:", documents);

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h4" component="h1">
              Document Dashboard
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
              onClick={handleUploadClick}
            >
              Upload Document
            </Button>
          </Box>
          <Typography variant="body1" color="text.secondary">
            Welcome, {user?.name || user?.email || 'User'}. Manage your financial documents here.
          </Typography>
        </Paper>

        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No documents found
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Upload your first financial document to get started.
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<CloudUploadIcon />}
              onClick={handleUploadClick}
            >
              Upload Document
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {documents.map((doc) => (
              <Grid item xs={12} sm={6} md={4} key={doc.id}>
                <Card elevation={2}>
                  <CardContent>
                    <Typography variant="h6" noWrap title={doc.filename}>
                      {doc.filename}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uploaded: {new Date(doc.created_at).toLocaleString()}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      <Typography variant="body2" mr={1}>
                        Status:
                      </Typography>
                      <Typography variant="body2" fontWeight="bold" color={getStatusColor(doc.status)}>
                        {doc.status}
                      </Typography>
                    </Box>
                  </CardContent>
                  <Divider />
                  <CardActions>
                    <Tooltip title="View Document">
                      <IconButton
                        color="primary"
                        onClick={() => handleViewDocument(doc.id.toString())}
                        disabled={doc.status.toUpperCase() === 'UPLOADING'}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    {doc.status.toUpperCase() === 'PROCESSING' && (
                      <Tooltip title="Cancel Processing">
                        <IconButton
                          color="warning"
                          onClick={() => handleCancelProcessing(doc.id.toString())}
                          disabled={cancellingDocuments.has(doc.id.toString())}
                        >
                          {cancellingDocuments.has(doc.id.toString()) ? (
                            <CircularProgress size={20} />
                          ) : (
                            <CancelIcon />
                          )}
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Delete Document">
                      <IconButton
                        color="error"
                        onClick={() => handleDeleteClick(doc.id.toString())}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)}>
        <DialogTitle>Upload Financial Document</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Select a financial document (PDF) to upload for analysis.
          </DialogContentText>
          <Box sx={{ mt: 2 }}>
            <input
              accept="application/pdf"
              style={{ display: 'none' }}
              id="raised-button-file"
              type="file"
              onChange={handleFileChange}
            />
            <label htmlFor="raised-button-file">
              <Button variant="outlined" component="span" fullWidth>
                Select File
              </Button>
            </label>
            {selectedFile && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Selected: {selectedFile.name}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)} disabled={uploading}>
            Cancel
          </Button>
          <Button 
            onClick={handleUpload} 
            color="primary" 
            disabled={!selectedFile || uploading}
            startIcon={uploading ? <CircularProgress size={20} /> : null}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this document? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleDelete} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard;

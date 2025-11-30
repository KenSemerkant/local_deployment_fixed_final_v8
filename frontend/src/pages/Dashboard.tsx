import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
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
  Tooltip,
  Chip,
  LinearProgress,
  Tabs,
  Tab,
  TextField
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  CloudUpload as CloudUploadIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Eye, Trash2, X, Plus, Clock, CheckCircle, AlertCircle, Download } from 'lucide-react';
import toast from 'react-hot-toast';
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
  const [downloadingDocuments, setDownloadingDocuments] = useState<Set<string>>(new Set());

  const { user } = useAuth();

  useEffect(() => {
    fetchDocuments();

    // Poll for updates every 5 seconds
    const intervalId = setInterval(() => {
      // Only poll if there are documents processing or if we just uploaded one
      // For simplicity, we'll poll always for now, or we could check if any doc is in 'processing' state
      fetchDocuments(true); // Pass silent flag to avoid loading spinner
    }, 5000);

    return () => clearInterval(intervalId);
  }, []);

  const fetchDocuments = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const docs = await documentService.getDocuments();
      setDocuments(docs);
      setError('');
    } catch (err: any) {
      console.error('Error fetching documents:', err);
      if (!silent) setError('Failed to load documents. Please try again.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const [uploadTab, setUploadTab] = useState(0);
  const [urlInput, setUrlInput] = useState('');

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const newDoc = await documentService.uploadDocument(selectedFile);
      setDocuments([...documents, newDoc]);
      setUploadDialogOpen(false);
      setSelectedFile(null);
      toast.success('Document uploaded successfully! 🎉');
    } catch (err: any) {
      console.error('Error uploading document:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to upload document. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleUrlUpload = async () => {
    if (!urlInput) return;

    setUploading(true);
    try {
      const newDoc = await documentService.uploadFromUrl(urlInput);
      console.log('New document from URL:', newDoc);

      if (newDoc && newDoc.id) {
        setDocuments(prevDocs => [...prevDocs, newDoc]);
        setUploadDialogOpen(false);
        setUrlInput('');
        toast.success('Document imported successfully! 🎉');
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err: any) {
      console.error('Error importing document:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to import document. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!documentToDelete) return;

    try {
      await documentService.deleteDocument(documentToDelete);
      setDocuments(documents.filter(doc => doc.id.toString() !== documentToDelete));
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
      toast.success('Document deleted successfully');
    } catch (err: any) {
      console.error('Error deleting document:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to delete document. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    }
  };

  const handleViewDocument = (documentId: string) => {
    window.location.href = `/documents/${documentId}`;
  };

  const handleDownload = async (documentId: string, filename: string) => {
    setDownloadingDocuments(prev => new Set(prev).add(documentId));
    try {
      await documentService.downloadDocument(documentId, filename);
      toast.success('Download started');
    } catch (err: any) {
      console.error('Error downloading document:', err);
      toast.error('Failed to download document');
    } finally {
      setDownloadingDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  const handleCancelProcessing = async (documentId: string) => {
    setCancellingDocuments(prev => new Set(prev).add(documentId));
    try {
      await documentService.cancelProcessing(documentId);
      toast.success('Document processing cancelled');
      // Refresh documents to update status
      fetchDocuments();
    } catch (err: any) {
      console.error('Error cancelling document processing:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to cancel document processing. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setCancellingDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  const getStatusColor = (status: string | undefined) => {
    if (!status) return 'text.secondary';
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

  const getStatusIcon = (status: string | undefined) => {
    if (!status) return <FileText size={16} />;
    switch (status.toUpperCase()) {
      case 'COMPLETED':
      case 'PROCESSED':
        return <CheckCircle size={16} />;
      case 'PROCESSING':
      case 'UPLOADED':
        return <Clock size={16} />;
      case 'ERROR':
        return <AlertCircle size={16} />;
      case 'CANCELLED':
        return <X size={16} />;
      default:
        return <FileText size={16} />;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 4,
            borderRadius: 3,
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography
                variant="h3"
                component="h1"
                sx={{
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  mb: 1,
                }}
              >
                📊 Document Dashboard
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 500 }}>
                Welcome back, {user?.full_name || user?.email || 'User'}! 👋
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mt: 1, opacity: 0.8 }}>
                Manage and analyze your financial documents with AI-powered insights
              </Typography>
            </Box>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                variant="contained"
                size="large"
                startIcon={<Plus size={20} />}
                onClick={() => setUploadDialogOpen(true)}
                sx={{
                  py: 1.5,
                  px: 3,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                    boxShadow: '0 6px 20px rgba(102, 126, 234, 0.6)',
                    transform: 'translateY(-1px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                Upload Document
              </Button>
            </motion.div>
          </Box>

          {documents.length > 0 && (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip
                label={`${documents.length} Total Documents`}
                color="primary"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
              <Chip
                label={`${documents.filter(d => d.status.toUpperCase() === 'COMPLETED').length} Processed`}
                color="success"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
              <Chip
                label={`${documents.filter(d => d.status.toUpperCase() === 'PROCESSING').length} Processing`}
                color="info"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
            </Box>
          )}
        </Paper>
      </motion.div>

      {/* Error alert */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
          >
            <Alert
              severity="error"
              sx={{
                mb: 3,
                borderRadius: 2,
                background: 'rgba(244, 67, 54, 0.1)',
                border: '1px solid rgba(244, 67, 54, 0.2)',
              }}
            >
              {error}
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading state */}
      {loading ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress size={60} thickness={4} />
              <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary' }}>
                Loading your documents...
              </Typography>
            </Box>
          </Box>
        </motion.div>
      ) : (
        <>
          {/* Empty state */}
          {documents.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 6,
                  textAlign: 'center',
                  borderRadius: 3,
                  background: 'rgba(255, 255, 255, 0.8)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
                }}
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.4, type: "spring" }}
                >
                  <Box
                    sx={{
                      width: 120,
                      height: 120,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 2rem',
                      boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)',
                    }}
                  >
                    <Upload size={48} color="white" />
                  </Box>
                </motion.div>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 2, color: 'text.primary' }}>
                  No documents yet
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
                  Upload your first financial document to unlock AI-powered insights and analysis
                </Typography>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<Upload size={20} />}
                    onClick={() => setUploadDialogOpen(true)}
                    sx={{
                      py: 1.5,
                      px: 4,
                      fontSize: '1.1rem',
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                        boxShadow: '0 6px 20px rgba(102, 126, 234, 0.6)',
                        transform: 'translateY(-1px)',
                      },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    Upload Your First Document
                  </Button>
                </motion.div>
              </Paper>
            </motion.div>
          ) : (
            /* Document grid */
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Grid container spacing={3}>
                <AnimatePresence>
                  {documents.map((doc, index) => {
                    if (!doc) return null;
                    return (
                      <Grid item xs={12} sm={6} md={4} key={doc.id || index}>
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          transition={{ duration: 0.4, delay: index * 0.1 }}
                          whileHover={{ y: -4 }}
                        >
                          <Card
                            elevation={0}
                            sx={{
                              height: '100%',
                              borderRadius: 3,
                              background: 'rgba(255, 255, 255, 0.9)',
                              backdropFilter: 'blur(20px)',
                              border: '1px solid rgba(255, 255, 255, 0.2)',
                              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                              transition: 'all 0.3s ease-in-out',
                              '&:hover': {
                                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.15)',
                                transform: 'translateY(-2px)',
                              },
                            }}
                          >
                            <CardContent sx={{ p: 3 }}>
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                                <Box
                                  sx={{
                                    width: 48,
                                    height: 48,
                                    borderRadius: 2,
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    mr: 2,
                                    flexShrink: 0,
                                  }}
                                >
                                  <FileText size={24} color="white" />
                                </Box>
                                <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                                  <Typography
                                    variant="h6"
                                    sx={{
                                      fontWeight: 600,
                                      mb: 0.5,
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                    }}
                                    title={doc.filename || 'Untitled'}
                                  >
                                    {doc.filename || 'Untitled'}
                                  </Typography>
                                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                    {doc.created_at ? new Date(doc.created_at).toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'short',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    }) : 'Unknown Date'}
                                  </Typography>
                                </Box>
                              </Box>

                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Chip
                                  icon={getStatusIcon(doc?.status)}
                                  label={doc?.status || 'UNKNOWN'}
                                  size="small"
                                  color={
                                    (doc?.status?.toUpperCase() === 'COMPLETED' || doc?.status?.toUpperCase() === 'PROCESSED')
                                      ? 'success'
                                      : (doc?.status?.toUpperCase() === 'PROCESSING' || doc?.status?.toUpperCase() === 'UPLOADED')
                                        ? 'info'
                                        : doc?.status?.toUpperCase() === 'ERROR'
                                          ? 'error'
                                          : 'warning'
                                  }
                                  sx={{
                                    fontWeight: 600,
                                    '& .MuiChip-icon': {
                                      fontSize: '1rem',
                                    },
                                  }}
                                />
                              </Box>

                              {doc?.status?.toUpperCase() === 'PROCESSING' && (
                                <Box sx={{ mb: 2 }}>
                                  <LinearProgress
                                    sx={{
                                      borderRadius: 1,
                                      height: 6,
                                      backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                      '& .MuiLinearProgress-bar': {
                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                      },
                                    }}
                                  />
                                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                    {doc?.processing_step || 'Processing document...'}
                                  </Typography>
                                </Box>
                              )}
                            </CardContent>

                            <Divider sx={{ opacity: 0.1 }} />

                            <CardActions sx={{ p: 2, justifyContent: 'space-between' }}>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                <Tooltip title="View Document">
                                  <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                                    <IconButton
                                      size="small"
                                      onClick={() => handleViewDocument(doc.id.toString())}
                                      disabled={doc.status.toUpperCase() === 'UPLOADING'}
                                      sx={{
                                        background: 'rgba(102, 126, 234, 0.1)',
                                        color: '#667eea',
                                        '&:hover': {
                                          background: 'rgba(102, 126, 234, 0.2)',
                                        },
                                      }}
                                    >
                                      <Eye size={16} />
                                    </IconButton>
                                  </motion.div>
                                </Tooltip>

                                {doc.status.toUpperCase() === 'PROCESSING' && (
                                  <Tooltip title="Cancel Processing">
                                    <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                                      <IconButton
                                        size="small"
                                        onClick={() => handleCancelProcessing(doc.id.toString())}
                                        disabled={cancellingDocuments.has(doc.id.toString())}
                                        sx={{
                                          background: 'rgba(255, 152, 0, 0.1)',
                                          color: '#ff9800',
                                          '&:hover': {
                                            background: 'rgba(255, 152, 0, 0.2)',
                                          },
                                        }}
                                      >
                                        {cancellingDocuments.has(doc.id.toString()) ? (
                                          <CircularProgress size={16} />
                                        ) : (
                                          <X size={16} />
                                        )}
                                      </IconButton>
                                    </motion.div>
                                  </Tooltip>
                                )}

                                <Tooltip title="Download Document">
                                  <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                                    <IconButton
                                      size="small"
                                      onClick={() => handleDownload(doc.id.toString(), doc.filename)}
                                      disabled={downloadingDocuments.has(doc.id.toString())}
                                      sx={{
                                        background: 'rgba(76, 175, 80, 0.1)',
                                        color: '#4caf50',
                                        '&:hover': {
                                          background: 'rgba(76, 175, 80, 0.2)',
                                        },
                                      }}
                                    >
                                      {downloadingDocuments.has(doc.id.toString()) ? (
                                        <CircularProgress size={16} />
                                      ) : (
                                        <Download size={16} />
                                      )}
                                    </IconButton>
                                  </motion.div>
                                </Tooltip>
                              </Box>

                              <Tooltip title="Delete Document">
                                <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                                  <IconButton
                                    size="small"
                                    onClick={() => {
                                      setDocumentToDelete(doc.id.toString());
                                      setDeleteDialogOpen(true);
                                    }}
                                    sx={{
                                      color: '#f44336',
                                      '&:hover': {
                                        background: 'rgba(244, 67, 54, 0.2)',
                                      },
                                    }}
                                  >
                                    <Trash2 size={16} />
                                  </IconButton>
                                </motion.div>
                              </Tooltip>
                            </CardActions>
                          </Card>
                        </motion.div>
                      </Grid>
                    );
                  })}
                </AnimatePresence>
              </Grid>
            </motion.div>
          )}
        </>
      )}

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Upload size={24} color="white" />
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Upload Document
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Add a new financial document for AI analysis
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={uploadTab} onChange={(e, v) => setUploadTab(v)} aria-label="upload tabs">
              <Tab label="File Upload" />
              <Tab label="Import from URL" />
            </Tabs>
          </Box>

          {uploadTab === 0 ? (
            <>
              <DialogContentText sx={{ mb: 3 }}>
                Select a financial document (PDF) to upload. Our AI will analyze it and provide intelligent insights.
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
                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <Button
                      variant="outlined"
                      component="span"
                      fullWidth
                      size="large"
                      startIcon={<FileText size={20} />}
                      sx={{
                        py: 2,
                        borderRadius: 2,
                        borderColor: '#667eea',
                        color: '#667eea',
                        borderStyle: 'dashed',
                        borderWidth: 2,
                        '&:hover': {
                          borderColor: '#5a6fd8',
                          backgroundColor: 'rgba(102, 126, 234, 0.05)',
                        },
                      }}
                    >
                      Choose PDF File
                    </Button>
                  </motion.div>
                </label>
                {selectedFile && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Paper
                      sx={{
                        mt: 2,
                        p: 2,
                        borderRadius: 2,
                        background: 'rgba(102, 126, 234, 0.1)',
                        border: '1px solid rgba(102, 126, 234, 0.2)',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <FileText size={20} color="#667eea" />
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {selectedFile.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                        </Box>
                        <CheckCircle size={20} color="#4caf50" />
                      </Box>
                    </Paper>
                  </motion.div>
                )}
              </Box>
            </>
          ) : (
            <>
              <DialogContentText sx={{ mb: 3 }}>
                Enter the URL of a financial document (PDF or HTML). We'll download and process it for you.
              </DialogContentText>
              <TextField
                autoFocus
                margin="dense"
                id="url"
                label="Document URL"
                type="url"
                fullWidth
                variant="outlined"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="https://example.com/report.pdf"
                sx={{ mb: 2 }}
              />
            </>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button
            onClick={() => setUploadDialogOpen(false)}
            disabled={uploading}
            sx={{ borderRadius: 2 }}
          >
            Cancel
          </Button>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button
              onClick={uploadTab === 0 ? handleUpload : handleUrlUpload}
              variant="contained"
              disabled={(uploadTab === 0 && !selectedFile) || (uploadTab === 1 && !urlInput) || uploading}
              startIcon={uploading ? <CircularProgress size={20} /> : <Upload size={20} />}
              sx={{
                borderRadius: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                },
              }}
            >
              {uploading ? 'Processing...' : (uploadTab === 0 ? 'Upload Document' : 'Import from URL')}
            </Button>
          </motion.div>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AlertCircle size={24} color="white" />
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Delete Document
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This action cannot be undone
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <DialogContentText sx={{ fontSize: '1rem' }}>
            Are you sure you want to delete this document? All associated data, analysis, and chat history will be permanently removed.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            sx={{ borderRadius: 2 }}
          >
            Cancel
          </Button>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button
              onClick={handleDelete}
              variant="contained"
              color="error"
              startIcon={<Trash2 size={20} />}
              sx={{
                borderRadius: 2,
                background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #e53935 0%, #c62828 100%)',
                },
              }}
            >
              Delete Document
            </Button>
          </motion.div>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard;
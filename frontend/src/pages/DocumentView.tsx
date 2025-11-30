import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  Menu,
  MenuItem
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { documentService, Document, KeyFigure } from '../services/api';
import ChatInterface from '../components/ChatInterface';
import MarkdownRenderer from '../components/MarkdownRenderer';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DocumentView: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();

  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [cancelling, setCancelling] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (documentId) {
      fetchDocument(documentId);
    }

    // Cleanup polling on unmount
    return () => {
      stopPolling();
    };
  }, [documentId]);

  const fetchDocument = async (id: string) => {
    setLoading(true);
    try {
      const doc = await documentService.getDocument(id);
      console.log("Document fetched:", doc);
      setDocument(doc);
      setError('');

      // Start polling if document is processing
      if (doc.status === 'PROCESSING' && !pollingInterval) {
        startPolling(id);
      } else if (doc.status !== 'PROCESSING' && pollingInterval) {
        stopPolling();
      }
    } catch (err: any) {
      console.error('Error fetching document:', err);
      setError('Failed to load document. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (id: string) => {
    if (pollingInterval) return; // Already polling

    console.log("Starting polling for document status updates");
    const interval = setInterval(async () => {
      try {
        const doc = await documentService.getDocument(id);
        setDocument(doc);

        // Stop polling if document is no longer processing
        if (doc.status !== 'PROCESSING') {
          console.log("Document processing completed, stopping polling");
          stopPolling();
        }
      } catch (err) {
        console.error('Error polling document:', err);
      }
    }, 3000); // Poll every 3 seconds

    setPollingInterval(interval);
  };

  const stopPolling = () => {
    if (pollingInterval) {
      console.log("Stopping polling");
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenuAnchor(null);
  };

  const handleCancelProcessing = async () => {
    if (!document) return;

    setCancelling(true);
    try {
      await documentService.cancelProcessing(document.id.toString());
      // Refresh document to show updated status
      fetchDocument(document.id.toString());
    } catch (err: any) {
      console.error('Error cancelling document processing:', err);
      setError('Failed to cancel document processing. Please try again.');
    } finally {
      setCancelling(false);
    }
  };

  const handleExport = async (format: 'txt' | 'csv') => {
    if (!documentId) return;

    try {
      const response = await documentService.exportDocument(documentId, format);
      window.open(response.export_url, '_blank');
    } catch (err: any) {
      console.error('Error exporting document:', err);
      setError('Failed to export document. Please try again.');
    } finally {
      handleExportClose();
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, mb: 4 }}>
          <Alert severity="error">{error}</Alert>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/dashboard')}
            sx={{ mt: 2 }}
          >
            Back to Dashboard
          </Button>
        </Box>
      </Container>
    );
  }

  if (!document) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, mb: 4 }}>
          <Alert severity="warning">Document not found</Alert>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/dashboard')}
            sx={{ mt: 2 }}
          >
            Back to Dashboard
          </Button>
        </Box>
      </Container>
    );
  }

  const isProcessing = document.status === 'PROCESSING' || document.status === 'UPLOADING';
  const hasError = document.status === 'ERROR';
  const isCancelled = document.status === 'CANCELLED';

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <IconButton onClick={() => navigate('/dashboard')} sx={{ mr: 1 }}>
                <ArrowBackIcon />
              </IconButton>
              <Typography variant="h4" component="h1" noWrap sx={{ maxWidth: '600px' }}>
                {document.filename}
              </Typography>
            </Box>
            <Box>
              {isProcessing && (
                <Tooltip title="Cancel Processing">
                  <IconButton
                    onClick={handleCancelProcessing}
                    disabled={cancelling}
                    color="warning"
                    sx={{ mr: 1 }}
                  >
                    {cancelling ? <CircularProgress size={20} /> : <CancelIcon />}
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title="Export Analysis">
                <IconButton onClick={handleExportClick} disabled={isProcessing || hasError || isCancelled}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
              <Menu
                anchorEl={exportMenuAnchor}
                open={Boolean(exportMenuAnchor)}
                onClose={handleExportClose}
              >
                <MenuItem onClick={() => handleExport('csv')}>Export as CSV</MenuItem>
                <MenuItem onClick={() => handleExport('txt')}>Export as Text</MenuItem>
              </Menu>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary" mr={2}>
              Uploaded: {new Date(document.created_at).toLocaleString()}
            </Typography>
            <Chip
              label={document.status}
              color={
                document.status === 'COMPLETED' ? 'success' :
                  document.status === 'ERROR' ? 'error' :
                    document.status === 'CANCELLED' ? 'warning' : 'info'
              }
              size="small"
            />
          </Box>
        </Paper>

        {isProcessing && (
          <Paper elevation={1} sx={{ p: 3, mb: 3, textAlign: 'center' }}>
            <CircularProgress size={40} sx={{ mb: 2 }} />
            <Typography variant="h6">
              Processing Document
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              {document.processing_step || 'Initializing processing...'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              This may take a few minutes depending on the document size.
            </Typography>
          </Paper>
        )}

        {hasError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body1" fontWeight="bold">
              Error processing document
            </Typography>
            <Typography variant="body2">
              {document.error_message || document.analysis_results?.error || 'An unknown error occurred during document processing.'}
            </Typography>
          </Alert>
        )}

        {isCancelled && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body1" fontWeight="bold">
              Document processing cancelled
            </Typography>
            <Typography variant="body2">
              The document processing was cancelled. You can upload the document again to restart processing.
            </Typography>
          </Alert>
        )}

        {!isProcessing && !hasError && !isCancelled && (
          <>
            <Paper elevation={1} sx={{ mb: 3 }}>
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                variant="fullWidth"
              >
                <Tab label="Summary" />
                <Tab label="Key Figures" />
                <Tab label="Chat" />
              </Tabs>

              <TabPanel value={tabValue} index={0}>
                <Typography variant="h6" gutterBottom>
                  Document Summary
                </Typography>
                <MarkdownRenderer
                  content={document.analysis_results?.summary || 'No summary available.'}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Typography variant="h6" gutterBottom>
                  Key Financial Figures
                </Typography>
                {document.analysis_results?.key_figures ? (
                  <Grid container spacing={2}>
                    {(() => {
                      try {
                        const figures = JSON.parse(document.analysis_results.key_figures);
                        return figures.map((figure: KeyFigure, index: number) => (
                          <Grid item xs={12} sm={6} md={4} key={index}>
                            <Card
                              elevation={0}
                              sx={{
                                height: '100%',
                                backgroundColor: (theme) => theme.palette.mode === 'light'
                                  ? 'rgba(64, 81, 137, 0.05)' // Very light primary color
                                  : 'rgba(255, 255, 255, 0.05)',
                                border: (theme) => `1px solid ${theme.palette.divider}`,
                                borderRadius: 2,
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                '&:hover': {
                                  transform: 'translateY(-2px)',
                                  boxShadow: (theme) => theme.shadows[2],
                                  backgroundColor: (theme) => theme.palette.mode === 'light'
                                    ? 'rgba(64, 81, 137, 0.08)'
                                    : 'rgba(255, 255, 255, 0.08)',
                                }
                              }}
                            >
                              <CardContent>
                                <Typography
                                  variant="h6"
                                  color="primary"
                                  sx={{ fontWeight: 700, mb: 1 }}
                                >
                                  {figure.value}
                                </Typography>
                                <Typography
                                  variant="body2"
                                  sx={{
                                    color: 'text.primary',
                                    fontWeight: 500,
                                    mb: 1
                                  }}
                                >
                                  {figure.name}
                                </Typography>
                                {figure.source_page && (
                                  <Chip
                                    label={`Page ${figure.source_page}`}
                                    size="small"
                                    sx={{
                                      height: 20,
                                      fontSize: '0.7rem',
                                      backgroundColor: (theme) => theme.palette.mode === 'light'
                                        ? 'rgba(255, 255, 255, 0.5)'
                                        : 'rgba(0, 0, 0, 0.2)',
                                    }}
                                  />
                                )}
                              </CardContent>
                            </Card>
                          </Grid>
                        ));
                      } catch (e) {
                        console.error("Error parsing key figures:", e);
                        return (
                          <Grid item xs={12}>
                            <Typography variant="body1" color="text.secondary">
                              Error parsing key figures data.
                            </Typography>
                          </Grid>
                        );
                      }
                    })()}
                  </Grid>
                ) : (
                  <Typography variant="body1" color="text.secondary">
                    No key figures extracted.
                  </Typography>
                )}
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                <ChatInterface
                  documentId={documentId!}
                  documentName={document.filename}
                />
              </TabPanel>
            </Paper>
          </>
        )}
      </Box>
    </Container>
  );
};

export default DocumentView;

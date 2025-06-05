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
  Divider,
  CircularProgress,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
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
  Send as SendIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { documentService, Document, KeyFigure, QuestionResponse } from '../services/api';

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
  const [question, setQuestion] = useState('');
  const [questionResponse, setQuestionResponse] = useState<QuestionResponse | null>(null);
  const [askingQuestion, setAskingQuestion] = useState(false);
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);

  useEffect(() => {
    if (documentId) {
      fetchDocument(documentId);
    }
  }, [documentId]);

  const fetchDocument = async (id: string) => {
    setLoading(true);
    try {
      const doc = await documentService.getDocument(id);
      console.log("Document fetched:", doc);
      setDocument(doc);
      setError('');
    } catch (err: any) {
      console.error('Error fetching document:', err);
      setError('Failed to load document. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleQuestionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !documentId) return;
    
    setAskingQuestion(true);
    try {
      const response = await documentService.askQuestion(documentId, question);
      setQuestionResponse(response);
    } catch (err: any) {
      console.error('Error asking question:', err);
      setError('Failed to get answer. Please try again.');
    } finally {
      setAskingQuestion(false);
    }
  };

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenuAnchor(null);
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
              <Tooltip title="Export Analysis">
                <IconButton onClick={handleExportClick} disabled={isProcessing || hasError}>
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
                document.status === 'ERROR' ? 'error' : 'info'
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
            <Typography variant="body1" color="text.secondary">
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
              {document.analysis_results?.error || 'An unknown error occurred during document processing.'}
            </Typography>
          </Alert>
        )}

        {!isProcessing && !hasError && (
          <>
            <Paper elevation={1} sx={{ mb: 3 }}>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange}
                variant="fullWidth"
              >
                <Tab label="Summary" />
                <Tab label="Key Figures" />
                <Tab label="Q&A" />
              </Tabs>

              <TabPanel value={tabValue} index={0}>
                <Typography variant="h6" gutterBottom>
                  Document Summary
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                  {document.analysis_results?.summary || 'No summary available.'}
                </Typography>
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
                            <Card variant="outlined">
                              <CardContent>
                                <Typography variant="h6" color="primary">
                                  {figure.value}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {figure.name}
                                </Typography>
                                {figure.source_page && (
                                  <Typography variant="caption" color="text.secondary">
                                    Source: Page {figure.source_page}
                                  </Typography>
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
                <Typography variant="h6" gutterBottom>
                  Ask Questions About This Document
                </Typography>
                <Box component="form" onSubmit={handleQuestionSubmit} sx={{ mb: 3 }}>
                  <TextField
                    fullWidth
                    label="Ask a question about this document"
                    variant="outlined"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={askingQuestion}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    endIcon={<SendIcon />}
                    disabled={!question.trim() || askingQuestion}
                  >
                    {askingQuestion ? 'Processing...' : 'Ask Question'}
                  </Button>
                </Box>

                {askingQuestion && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                    <CircularProgress />
                  </Box>
                )}

                {questionResponse && (
                  <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Answer
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 2, whiteSpace: 'pre-line' }}>
                      {questionResponse.answer}
                    </Typography>
                    
                    {questionResponse.sources && questionResponse.sources.length > 0 && (
                      <>
                        <Divider sx={{ my: 2 }} />
                        <Typography variant="subtitle2" gutterBottom>
                          Sources
                        </Typography>
                        <List dense>
                          {questionResponse.sources.map((source, index) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={source.snippet}
                                secondary={source.page ? `Page ${source.page}` : undefined}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}
                  </Paper>
                )}
              </TabPanel>
            </Paper>
          </>
        )}
      </Box>
    </Container>
  );
};

export default DocumentView;

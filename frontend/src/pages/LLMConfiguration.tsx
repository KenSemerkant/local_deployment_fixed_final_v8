import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Card,
  CardContent,
  CardActions,
  Alert,
  Snackbar,
  CircularProgress,
  Chip,
  Divider,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Science as TestIcon
} from '@mui/icons-material';
import axios from 'axios';

interface LLMVendor {
  name: string;
  description: string;
  requires_api_key: boolean;
  default_base_url: string | null;
  default_models: string[];
  langchain_class: string;
}

interface LLMConfig {
  vendor: string;
  api_key?: string;
  base_url?: string;
  model?: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
}

interface LLMConfigResponse {
  current_vendor: string;
  current_model?: string;
  current_config: LLMConfig;
  available_vendors: string[];
  vendor_models: Record<string, string[]>;
  status: string;
  error?: string;
}

const LLMConfiguration: React.FC = () => {
  const [config, setConfig] = useState<LLMConfig>({
    vendor: 'openai',
    api_key: '',
    base_url: '',
    model: '',
    temperature: 0.3,
    max_tokens: 2000,
    timeout: 300
  });
  
  const [vendors, setVendors] = useState<Record<string, LLMVendor>>({});
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [refreshingModels, setRefreshingModels] = useState(false);
  
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info'
  });

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadConfiguration();
    loadVendors();
  }, []);

  useEffect(() => {
    if (config.vendor) {
      loadModelsForVendor(config.vendor);
    }
  }, [config.vendor, config.base_url]);

  const loadConfiguration = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/llm/config`);
      const data: LLMConfigResponse = response.data;
      
      setConfig(data.current_config);
      
      if (data.error) {
        showSnackbar(data.error, 'error');
      }
    } catch (error: any) {
      console.error('Error loading LLM configuration:', error);
      showSnackbar('Error loading LLM configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadVendors = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/llm/vendors`);
      setVendors(response.data.vendors);
    } catch (error: any) {
      console.error('Error loading vendors:', error);
      showSnackbar('Error loading vendors', 'error');
    }
  };

  const loadModelsForVendor = async (vendor: string) => {
    try {
      setRefreshingModels(true);
      const params: any = {};
      if (config.base_url) {
        params.base_url = config.base_url;
      }
      if (config.api_key) {
        params.api_key = config.api_key;
      }

      const response = await axios.get(`${API_URL}/admin/llm/models/${vendor}`, { params });
      setAvailableModels(response.data.models || []);
      
      if (response.data.error) {
        showSnackbar(`Warning: ${response.data.error}`, 'info');
      }
    } catch (error: any) {
      console.error('Error loading models:', error);
      // Fallback to default models
      if (vendors[vendor]) {
        setAvailableModels(vendors[vendor].default_models);
      }
      showSnackbar('Could not fetch live models, showing defaults', 'info');
    } finally {
      setRefreshingModels(false);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleConfigChange = (field: keyof LLMConfig, value: any) => {
    setConfig({ ...config, [field]: value });
  };

  const handleVendorChange = (vendor: string) => {
    const vendorInfo = vendors[vendor];
    if (vendorInfo) {
      setConfig({
        ...config,
        vendor,
        base_url: vendorInfo.default_base_url || '',
        model: vendorInfo.default_models[0] || '',
        api_key: vendorInfo.requires_api_key ? config.api_key : ''
      });
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await axios.post(`${API_URL}/admin/llm/config`, config);
      showSnackbar('LLM configuration saved successfully', 'success');
    } catch (error: any) {
      console.error('Error saving configuration:', error);
      const message = error.response?.data?.detail || 'Error saving configuration';
      showSnackbar(message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      const response = await axios.post(`${API_URL}/admin/llm/test`, config);
      
      if (response.data.success) {
        showSnackbar('Connection test successful!', 'success');
      } else {
        showSnackbar(`Connection test failed: ${response.data.error}`, 'error');
      }
    } catch (error: any) {
      console.error('Error testing configuration:', error);
      const message = error.response?.data?.detail || 'Error testing configuration';
      showSnackbar(message, 'error');
    } finally {
      setTesting(false);
    }
  };

  const currentVendor = vendors[config.vendor];

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
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SettingsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          LLM Configuration
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Configure the Large Language Model provider for your AI Financial Analyst
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Main Configuration */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Provider Configuration
            </Typography>
            
            {/* Vendor Selection */}
            <FormControl fullWidth margin="normal">
              <InputLabel>LLM Provider</InputLabel>
              <Select
                value={config.vendor}
                onChange={(e) => handleVendorChange(e.target.value)}
                label="LLM Provider"
              >
                {Object.entries(vendors).map(([key, vendor]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {vendor.name}
                      {vendor.requires_api_key && (
                        <Chip label="API Key Required" size="small" color="warning" />
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {currentVendor && (
              <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
                <strong>{currentVendor.name}:</strong> {currentVendor.description}
                <br />
                <strong>LangChain Integration:</strong> {currentVendor.langchain_class}
              </Alert>
            )}

            {/* API Key */}
            {currentVendor?.requires_api_key && (
              <TextField
                fullWidth
                label="API Key"
                type="password"
                value={config.api_key || ''}
                onChange={(e) => handleConfigChange('api_key', e.target.value)}
                margin="normal"
                required
                helperText="Your API key will be stored securely"
              />
            )}

            {/* Base URL */}
            <TextField
              fullWidth
              label="Base URL"
              value={config.base_url || ''}
              onChange={(e) => handleConfigChange('base_url', e.target.value)}
              margin="normal"
              helperText={currentVendor?.default_base_url ? `Default: ${currentVendor.default_base_url}` : 'Custom endpoint URL'}
            />

            {/* Model Selection */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Model</InputLabel>
                <Select
                  value={config.model || ''}
                  onChange={(e) => handleConfigChange('model', e.target.value)}
                  label="Model"
                >
                  {availableModels.map((model) => (
                    <MenuItem key={model} value={model}>
                      {model}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="outlined"
                onClick={() => loadModelsForVendor(config.vendor)}
                disabled={refreshingModels}
                sx={{ minWidth: 'auto', p: 1 }}
              >
                {refreshingModels ? <CircularProgress size={20} /> : <RefreshIcon />}
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Advanced Settings */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Advanced Settings</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Temperature"
                      type="number"
                      value={config.temperature}
                      onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                      inputProps={{ min: 0, max: 2, step: 0.1 }}
                      helperText="0.0 = deterministic, 2.0 = very creative"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Max Tokens"
                      type="number"
                      value={config.max_tokens}
                      onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value))}
                      inputProps={{ min: 1, max: 32000 }}
                      helperText="Maximum response length"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Timeout (seconds)"
                      type="number"
                      value={config.timeout}
                      onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value))}
                      inputProps={{ min: 10, max: 600 }}
                      helperText="Request timeout"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            {/* Action Buttons */}
            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={saving}
                startIcon={saving ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </Button>
              <Button
                variant="outlined"
                onClick={handleTest}
                disabled={testing}
                startIcon={testing ? <CircularProgress size={20} /> : <TestIcon />}
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Current Status */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Current Configuration
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Provider"
                  secondary={currentVendor?.name || config.vendor}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Model"
                  secondary={config.model || 'Not selected'}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Temperature"
                  secondary={config.temperature}
                />
              </ListItem>
            </List>
          </Paper>

          {/* Supported Providers */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Supported Providers
            </Typography>
            <List dense>
              {Object.entries(vendors).map(([key, vendor]) => (
                <ListItem key={key}>
                  <ListItemIcon>
                    {vendor.requires_api_key ? (
                      <ErrorIcon color="warning" />
                    ) : (
                      <CheckCircleIcon color="success" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={vendor.name}
                    secondary={vendor.description}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>

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

export default LLMConfiguration;

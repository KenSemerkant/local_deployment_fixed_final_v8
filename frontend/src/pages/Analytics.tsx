import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  LinearProgress,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  ThumbUp as ThumbUpIcon,
  Token as TokenIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Storage as StorageIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Star as StarIcon,
  Comment as CommentIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts';
import axios from 'axios';

interface AnalyticsOverview {
  period_days: number;
  users: {
    total: number;
    active_in_period: number;
    activity_rate: number;
  };
  documents: {
    total: number;
    uploaded_in_period: number;
  };
  questions: {
    total: number;
    asked_in_period: number;
  };
  tokens: {
    total_tokens: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost: number;
  };
  performance: {
    avg_analysis_time_seconds: number;
    avg_question_time_seconds: number;
  };
  feedback: {
    average_rating: number;
    total_feedback: number;
    helpful_responses: number;
    unhelpful_responses: number;
    satisfaction_rate: number;
  };
}

interface UsagePatterns {
  hourly_usage: Array<{ hour: number; events: number }>;
  daily_usage: Array<{ date: string; events: number }>;
  top_users: Array<{ email: string; name: string; activity_count: number }>;
  operation_stats: Array<{ operation: string; count: number }>;
}

interface TokenAnalytics {
  vendor_usage: Array<{ vendor: string; total_tokens: number; total_cost: number; operation_count: number }>;
  operation_usage: Array<{ operation: string; total_tokens: number; avg_tokens: number; total_cost: number }>;
  daily_trend: Array<{ date: string; tokens: number; cost: number }>;
  top_users: Array<{ email: string; name: string; total_tokens: number; total_cost: number }>;
}

interface PerformanceAnalytics {
  operation_performance: Array<{
    operation: string;
    avg_duration: number;
    min_duration: number;
    max_duration: number;
    operation_count: number;
    success_rate: number;
  }>;
  daily_performance: Array<{ date: string; avg_duration: number; operation_count: number }>;
  file_size_correlation: Array<{ file_size_mb: number; duration_seconds: number }>;
  error_rates: Array<{ operation: string; total_operations: number; error_count: number; error_rate: number }>;
}

interface UserSatisfaction {
  overall_satisfaction: {
    average_rating: number;
    total_feedback: number;
    positive_rate: number;
    negative_rate: number;
    helpful_rate: number;
  };
  feedback_by_type: Array<{ type: string; avg_rating: number; count: number }>;
  daily_satisfaction: Array<{ date: string; avg_rating: number; feedback_count: number }>;
  recent_comments: Array<{ comment: string; rating: number; timestamp: string; user_email: string }>;
}

const Analytics: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [usagePatterns, setUsagePatterns] = useState<UsagePatterns | null>(null);
  const [tokenAnalytics, setTokenAnalytics] = useState<TokenAnalytics | null>(null);
  const [performanceAnalytics, setPerformanceAnalytics] = useState<PerformanceAnalytics | null>(null);
  const [userSatisfaction, setUserSatisfaction] = useState<UserSatisfaction | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info' | 'warning'
  });

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Load all analytics data in parallel
      const [
        overviewResponse,
        usagePatternsResponse,
        tokenAnalyticsResponse,
        performanceAnalyticsResponse,
        userSatisfactionResponse
      ] = await Promise.all([
        axios.get(`${API_URL}/admin/analytics/overview?days=${selectedPeriod}`),
        axios.get(`${API_URL}/admin/analytics/usage-patterns?days=${selectedPeriod}`),
        axios.get(`${API_URL}/admin/analytics/tokens?days=${selectedPeriod}`),
        axios.get(`${API_URL}/admin/analytics/performance?days=${selectedPeriod}`),
        axios.get(`${API_URL}/admin/analytics/satisfaction?days=${selectedPeriod}`)
      ]);
      
      setOverview(overviewResponse.data);
      setUsagePatterns(usagePatternsResponse.data);
      setTokenAnalytics(tokenAnalyticsResponse.data);
      setPerformanceAnalytics(performanceAnalyticsResponse.data);
      setUserSatisfaction(userSatisfactionResponse.data);
      
    } catch (error: any) {
      console.error('Error loading analytics data:', error);
      showSnackbar('Error loading analytics data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadAnalyticsData();
    setRefreshing(false);
    showSnackbar('Analytics data refreshed', 'success');
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
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
            <AnalyticsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            System Analytics
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Comprehensive insights into system usage, performance, and user satisfaction
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={selectedPeriod}
              label="Period"
              onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
              <MenuItem value={365}>Last year</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            onClick={refreshData}
            disabled={refreshing}
            startIcon={refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Overview Cards */}
      {overview && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <PersonIcon color="primary" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Active Users
                    </Typography>
                    <Typography variant="h4" component="div">
                      {overview.users.active_in_period}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {overview.users.activity_rate.toFixed(1)}% of total
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <TokenIcon color="success" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Tokens
                    </Typography>
                    <Typography variant="h4" component="div">
                      {formatNumber(overview.tokens.total_tokens)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatCurrency(overview.tokens.estimated_cost)} cost
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <SpeedIcon color="warning" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Avg Response Time
                    </Typography>
                    <Typography variant="h4" component="div">
                      {formatDuration(overview.performance.avg_question_time_seconds)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Questions answered
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <StarIcon color="error" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      User Satisfaction
                    </Typography>
                    <Typography variant="h4" component="div">
                      {overview.feedback.average_rating.toFixed(1)}/5
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {overview.feedback.satisfaction_rate.toFixed(1)}% helpful
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Usage Patterns */}
      {usagePatterns && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Usage Patterns
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Hourly Activity
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={usagePatterns.hourly_usage}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <RechartsTooltip />
                  <Area type="monotone" dataKey="events" stroke="#8884d8" fill="#8884d8" />
                </AreaChart>
              </ResponsiveContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Daily Activity Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={usagePatterns.daily_usage}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="events" stroke="#82ca9d" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Top Active Users
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>User</TableCell>
                      <TableCell align="right">Activity Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {usagePatterns.top_users.slice(0, 5).map((user, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {user.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {user.email}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Chip label={user.activity_count} size="small" color="primary" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Operation Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={usagePatterns.operation_stats}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ operation, percent }) => `${operation} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {usagePatterns.operation_stats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Token Analytics */}
      {tokenAnalytics && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Token Usage Analytics
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Usage by Vendor
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={tokenAnalytics.vendor_usage}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="vendor" />
                  <YAxis />
                  <RechartsTooltip formatter={(value, name) => [
                    name === 'total_tokens' ? formatNumber(value as number) : formatCurrency(value as number),
                    name === 'total_tokens' ? 'Tokens' : 'Cost'
                  ]} />
                  <Bar dataKey="total_tokens" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Daily Token Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={tokenAnalytics.daily_trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <RechartsTooltip />
                  <Line yAxisId="left" type="monotone" dataKey="tokens" stroke="#8884d8" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="cost" stroke="#82ca9d" strokeWidth={2} />
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Token Usage by Operation
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Operation</TableCell>
                      <TableCell align="right">Total Tokens</TableCell>
                      <TableCell align="right">Avg Tokens</TableCell>
                      <TableCell align="right">Total Cost</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tokenAnalytics.operation_usage.map((op, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Chip label={op.operation} variant="outlined" />
                        </TableCell>
                        <TableCell align="right">{formatNumber(op.total_tokens)}</TableCell>
                        <TableCell align="right">{formatNumber(op.avg_tokens)}</TableCell>
                        <TableCell align="right">{formatCurrency(op.total_cost)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Performance Analytics */}
      {performanceAnalytics && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Performance Analytics
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Operation Performance
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Operation</TableCell>
                      <TableCell align="right">Avg Duration</TableCell>
                      <TableCell align="right">Success Rate</TableCell>
                      <TableCell align="right">Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {performanceAnalytics.operation_performance.map((op, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Chip label={op.operation} variant="outlined" size="small" />
                        </TableCell>
                        <TableCell align="right">{formatDuration(op.avg_duration)}</TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={op.success_rate}
                              sx={{ width: 50, height: 6 }}
                              color={op.success_rate > 95 ? 'success' : op.success_rate > 90 ? 'warning' : 'error'}
                            />
                            <Typography variant="body2">{op.success_rate.toFixed(1)}%</Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">{op.operation_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                File Size vs Processing Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart data={performanceAnalytics.file_size_correlation}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="file_size_mb" name="File Size (MB)" />
                  <YAxis dataKey="duration_seconds" name="Duration (s)" />
                  <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter name="Processing Time" data={performanceAnalytics.file_size_correlation} fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Daily Performance Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceAnalytics.daily_performance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <RechartsTooltip />
                  <Line yAxisId="left" type="monotone" dataKey="avg_duration" stroke="#8884d8" strokeWidth={2} name="Avg Duration (s)" />
                  <Line yAxisId="right" type="monotone" dataKey="operation_count" stroke="#82ca9d" strokeWidth={2} name="Operation Count" />
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* User Satisfaction */}
      {userSatisfaction && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Satisfaction
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <StarIcon color="warning" sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h4" component="div">
                        {userSatisfaction.overall_satisfaction.average_rating.toFixed(1)}/5
                      </Typography>
                      <Typography color="textSecondary">
                        Average Rating
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Positive Rate:</Typography>
                    <Typography variant="body2" color="success.main">
                      {userSatisfaction.overall_satisfaction.positive_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Helpful Rate:</Typography>
                    <Typography variant="body2" color="primary.main">
                      {userSatisfaction.overall_satisfaction.helpful_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Total Feedback:</Typography>
                    <Typography variant="body2">
                      {userSatisfaction.overall_satisfaction.total_feedback}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={8}>
              <Typography variant="subtitle1" gutterBottom>
                Satisfaction Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={userSatisfaction.daily_satisfaction}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 5]} />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="avg_rating" stroke="#ff7300" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Recent User Comments
              </Typography>
              <List>
                {userSatisfaction.recent_comments.slice(0, 5).map((comment, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemIcon>
                        <CommentIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body1">"{comment.comment}"</Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              {[...Array(5)].map((_, i) => (
                                <StarIcon
                                  key={i}
                                  sx={{
                                    fontSize: 16,
                                    color: i < comment.rating ? 'warning.main' : 'grey.300'
                                  }}
                                />
                              ))}
                            </Box>
                          </Box>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              {comment.user_email}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(comment.timestamp).toLocaleDateString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < userSatisfaction.recent_comments.slice(0, 5).length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Grid>
          </Grid>
        </Paper>
      )}

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

export default Analytics;

import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Typography,
    Paper,
    TextField,
    Button,
    Avatar,
    Grid,
    Alert,
    CircularProgress,
    IconButton,
    useTheme
} from '@mui/material';
import { Camera, Save, User, Mail, Lock } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { authService, storageService } from '../services/api';

const Profile = () => {
    const { user, login } = useAuth();
    const theme = useTheme();
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
    const [avatarFile, setAvatarFile] = useState<File | null>(null);

    useEffect(() => {
        if (user) {
            setFormData(prev => ({
                ...prev,
                full_name: user.full_name || '',
                email: user.email || ''
            }));
            if (user.avatar_url) {
                // Construct full URL if it's a relative path
                const url = user.avatar_url.startsWith('http')
                    ? user.avatar_url
                    : `${process.env.REACT_APP_API_URL}${user.avatar_url}`;
                setAvatarPreview(url);
            }
        }
    }, [user]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setAvatarFile(file);
            setAvatarPreview(URL.createObjectURL(file));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            if (formData.password && formData.password !== formData.confirmPassword) {
                throw new Error("Passwords don't match");
            }

            let avatarUrl = user?.avatar_url;

            // Upload avatar if changed
            if (avatarFile) {
                const uploadResult = await storageService.uploadAvatar(avatarFile);
                avatarUrl = uploadResult.url;
            }

            // Update profile
            const updateData: any = {
                full_name: formData.full_name,
                email: formData.email,
                avatar_url: avatarUrl
            };

            if (formData.password) {
                updateData.password = formData.password;
            }

            const updatedUser = await authService.updateProfile(updateData);

            // Update local user context (hacky way, ideally AuthContext exposes an update method)
            // We can re-login with the token to refresh user data or just reload
            // For now, let's assume login updates the user state
            // Actually, we should probably just reload the page or fetch user/me
            // But since we don't have a refreshUser method in context yet, let's just show success

            setSuccess('Profile updated successfully!');
            setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));

        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="md" sx={{ py: 4 }}>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Paper
                    elevation={0}
                    sx={{
                        p: 4,
                        borderRadius: 4,
                        background: theme.palette.mode === 'dark'
                            ? 'rgba(30, 41, 59, 0.8)'
                            : 'rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid',
                        borderColor: theme.palette.mode === 'dark'
                            ? 'rgba(255, 255, 255, 0.1)'
                            : 'rgba(255, 255, 255, 0.5)',
                    }}
                >
                    <Typography variant="h4" fontWeight="bold" gutterBottom sx={{ mb: 4 }}>
                        Profile Settings
                    </Typography>

                    {error && (
                        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                            {error}
                        </Alert>
                    )}

                    {success && (
                        <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                            {success}
                        </Alert>
                    )}

                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={4}>
                            <Grid item xs={12} md={4} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                <Box sx={{ position: 'relative' }}>
                                    <Avatar
                                        src={avatarPreview || undefined}
                                        sx={{
                                            width: 150,
                                            height: 150,
                                            mb: 2,
                                            border: '4px solid',
                                            borderColor: 'primary.main',
                                            fontSize: '3rem'
                                        }}
                                    >
                                        {formData.full_name?.charAt(0).toUpperCase() || 'U'}
                                    </Avatar>
                                    <input
                                        accept="image/*"
                                        style={{ display: 'none' }}
                                        id="avatar-upload"
                                        type="file"
                                        onChange={handleAvatarChange}
                                    />
                                    <label htmlFor="avatar-upload">
                                        <IconButton
                                            component="span"
                                            sx={{
                                                position: 'absolute',
                                                bottom: 16,
                                                right: 0,
                                                background: theme.palette.primary.main,
                                                color: 'white',
                                                '&:hover': {
                                                    background: theme.palette.primary.dark,
                                                }
                                            }}
                                        >
                                            <Camera size={20} />
                                        </IconButton>
                                    </label>
                                </Box>
                                <Typography variant="caption" color="text.secondary" align="center">
                                    Click the camera icon to update your photo
                                </Typography>
                            </Grid>

                            <Grid item xs={12} md={8}>
                                <Grid container spacing={3}>
                                    <Grid item xs={12}>
                                        <TextField
                                            fullWidth
                                            label="Full Name"
                                            name="full_name"
                                            value={formData.full_name}
                                            onChange={handleChange}
                                            InputProps={{
                                                startAdornment: <User size={20} style={{ marginRight: 8, opacity: 0.5 }} />,
                                            }}
                                        />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField
                                            fullWidth
                                            label="Email Address"
                                            name="email"
                                            type="email"
                                            value={formData.email}
                                            onChange={handleChange}
                                            InputProps={{
                                                startAdornment: <Mail size={20} style={{ marginRight: 8, opacity: 0.5 }} />,
                                            }}
                                        />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Typography variant="h6" sx={{ mb: 2, mt: 2 }}>
                                            Change Password
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={12} md={6}>
                                        <TextField
                                            fullWidth
                                            label="New Password"
                                            name="password"
                                            type="password"
                                            value={formData.password}
                                            onChange={handleChange}
                                            InputProps={{
                                                startAdornment: <Lock size={20} style={{ marginRight: 8, opacity: 0.5 }} />,
                                            }}
                                        />
                                    </Grid>
                                    <Grid item xs={12} md={6}>
                                        <TextField
                                            fullWidth
                                            label="Confirm Password"
                                            name="confirmPassword"
                                            type="password"
                                            value={formData.confirmPassword}
                                            onChange={handleChange}
                                            InputProps={{
                                                startAdornment: <Lock size={20} style={{ marginRight: 8, opacity: 0.5 }} />,
                                            }}
                                        />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Button
                                            type="submit"
                                            variant="contained"
                                            size="large"
                                            disabled={loading}
                                            startIcon={loading ? <CircularProgress size={20} /> : <Save size={20} />}
                                            sx={{
                                                mt: 2,
                                                px: 4,
                                                py: 1.5,
                                                borderRadius: 2,
                                                textTransform: 'none',
                                                fontSize: '1rem',
                                                fontWeight: 600
                                            }}
                                        >
                                            {loading ? 'Saving...' : 'Save Changes'}
                                        </Button>
                                    </Grid>
                                </Grid>
                            </Grid>
                        </Grid>
                    </form>
                </Paper>
            </motion.div>
        </Container>
    );
};

export default Profile;

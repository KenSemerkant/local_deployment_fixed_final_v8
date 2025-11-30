import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme, Theme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

type ColorMode = 'light' | 'dark';

interface ThemeContextType {
    mode: ColorMode;
    toggleColorMode: () => void;
    theme: Theme;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useColorMode = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useColorMode must be used within a ThemeProvider');
    }
    return context;
};

interface ThemeProviderProps {
    children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
    const [mode, setMode] = useState<ColorMode>(() => {
        const savedMode = localStorage.getItem('themeMode');
        return (savedMode as ColorMode) || 'light';
    });

    useEffect(() => {
        localStorage.setItem('themeMode', mode);
    }, [mode]);

    const toggleColorMode = () => {
        setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
    };

    const theme = React.useMemo(
        () =>
            createTheme({
                palette: {
                    mode,
                    primary: {
                        main: '#405189', // Velzon Blue
                        light: '#667eea',
                        dark: '#364574',
                        contrastText: '#ffffff',
                    },
                    secondary: {
                        main: '#0ab39c', // Velzon Teal
                        light: '#3bc9b6',
                        dark: '#088f7d',
                        contrastText: '#ffffff',
                    },
                    success: {
                        main: '#0ab39c',
                        contrastText: '#ffffff',
                    },
                    info: {
                        main: '#299cdb',
                        contrastText: '#ffffff',
                    },
                    warning: {
                        main: '#f7b84b',
                        contrastText: '#ffffff',
                    },
                    error: {
                        main: '#f06548',
                        contrastText: '#ffffff',
                    },
                    background: {
                        default: mode === 'light' ? '#f3f3f9' : '#1a1d21', // Velzon Light/Dark backgrounds
                        paper: mode === 'light' ? '#ffffff' : '#212529',   // Velzon Card backgrounds
                    },
                    text: {
                        primary: mode === 'light' ? '#212529' : '#ced4da',
                        secondary: mode === 'light' ? '#878a99' : '#878a99',
                    },
                    divider: mode === 'light' ? '#e9ebec' : 'rgba(255, 255, 255, 0.1)',
                },
                typography: {
                    fontFamily: [
                        'Inter',
                        'Roboto',
                        '-apple-system',
                        'BlinkMacSystemFont',
                        'Segoe UI',
                        'sans-serif',
                    ].join(','),
                    fontSize: 13, // Velzon uses a slightly smaller base font size (0.8125rem)
                    h1: {
                        fontWeight: 600,
                        fontSize: '2.25rem', // 36px
                        lineHeight: 1.2,
                    },
                    h2: {
                        fontWeight: 600,
                        fontSize: '1.875rem', // 30px
                        lineHeight: 1.2,
                    },
                    h3: {
                        fontWeight: 600,
                        fontSize: '1.5rem', // 24px
                        lineHeight: 1.2,
                    },
                    h4: {
                        fontWeight: 600,
                        fontSize: '1.125rem', // 18px
                        lineHeight: 1.2,
                    },
                    h5: {
                        fontWeight: 600,
                        fontSize: '1rem', // 16px
                        lineHeight: 1.2,
                    },
                    h6: {
                        fontWeight: 600,
                        fontSize: '0.875rem', // 14px
                        lineHeight: 1.2,
                    },
                    body1: {
                        fontSize: '0.875rem', // 14px
                        lineHeight: 1.5,
                    },
                    body2: {
                        fontSize: '0.8125rem', // 13px
                        lineHeight: 1.5,
                    },
                    button: {
                        fontWeight: 500,
                        textTransform: 'none',
                        fontSize: '0.875rem',
                    },
                    subtitle1: {
                        fontSize: '1rem',
                        fontWeight: 500,
                    },
                    subtitle2: {
                        fontSize: '0.875rem',
                        fontWeight: 500,
                    },
                },
                shape: {
                    borderRadius: 4, // More subtle border radius like Velzon
                },
                components: {
                    MuiButton: {
                        styleOverrides: {
                            root: {
                                borderRadius: 4,
                                padding: '8px 16px',
                                boxShadow: 'none',
                                '&:hover': {
                                    boxShadow: '0 5px 10px rgba(30, 32, 37, 0.12)',
                                    transform: 'translateY(-1px)',
                                },
                            },
                            contained: {
                                // Remove gradient, use solid primary color
                                backgroundColor: '#405189',
                                '&:hover': {
                                    backgroundColor: '#364574',
                                },
                            },
                        },
                    },
                    MuiPaper: {
                        styleOverrides: {
                            root: {
                                backgroundImage: 'none',
                                border: 'none',
                                boxShadow: mode === 'light'
                                    ? '0 1px 2px rgba(56, 65, 74, 0.15)'
                                    : '0 1px 2px rgba(0, 0, 0, 0.15)',
                            },
                        },
                    },
                    MuiCard: {
                        styleOverrides: {
                            root: {
                                borderRadius: 4,
                                border: 'none',
                                boxShadow: mode === 'light'
                                    ? '0 1px 2px rgba(56, 65, 74, 0.15)'
                                    : '0 1px 2px rgba(0, 0, 0, 0.15)',
                                transition: 'all 0.2s ease-in-out',
                                '&:hover': {
                                    transform: 'translateY(-2px)',
                                    boxShadow: '0 5px 10px rgba(30, 32, 37, 0.12)',
                                },
                            },
                        },
                    },
                    MuiAppBar: {
                        styleOverrides: {
                            root: {
                                background: mode === 'light' ? '#ffffff' : '#212529',
                                color: mode === 'light' ? '#212529' : '#ced4da',
                                boxShadow: '0 1px 2px rgba(56, 65, 74, 0.15)',
                                borderBottom: 'none',
                            },
                        },
                    },
                    MuiDrawer: {
                        styleOverrides: {
                            paper: {
                                backgroundColor: '#405189', // Sidebar is typically dark blue in Velzon
                                color: '#ffffff',
                                borderRight: 'none',
                            }
                        }
                    }
                },
            }),
        [mode]
    );

    return (
        <ThemeContext.Provider value={{ mode, toggleColorMode, theme }}>
            <MuiThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </MuiThemeProvider>
        </ThemeContext.Provider>
    );
};

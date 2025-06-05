import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Typography, Box, Divider, useTheme, alpha } from '@mui/material';
import { styled } from '@mui/material/styles';

interface MarkdownRendererProps {
  content: string;
  variant?: 'body1' | 'body2';
}

const StyledMarkdownContainer = styled(Box)(({ theme }) => ({
  '& h1': {
    ...theme.typography.h4,
    color: theme.palette.text.primary,
    marginTop: theme.spacing(3),
    marginBottom: theme.spacing(2),
    fontWeight: 600,
    '&:first-of-type': {
      marginTop: 0,
    },
  },
  '& h2': {
    ...theme.typography.h5,
    color: theme.palette.text.primary,
    marginTop: theme.spacing(2.5),
    marginBottom: theme.spacing(1.5),
    fontWeight: 600,
  },
  '& h3': {
    ...theme.typography.h6,
    color: theme.palette.text.primary,
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(1),
    fontWeight: 600,
  },
  '& h4, & h5, & h6': {
    ...theme.typography.subtitle1,
    color: theme.palette.text.primary,
    marginTop: theme.spacing(1.5),
    marginBottom: theme.spacing(1),
    fontWeight: 600,
  },
  '& p': {
    ...theme.typography.body1,
    color: theme.palette.text.primary,
    marginBottom: theme.spacing(1.5),
    lineHeight: 1.7,
    '&:last-child': {
      marginBottom: 0,
    },
  },
  '& ul, & ol': {
    marginBottom: theme.spacing(1.5),
    paddingLeft: theme.spacing(3),
  },
  '& li': {
    ...theme.typography.body1,
    color: theme.palette.text.primary,
    marginBottom: theme.spacing(0.5),
    lineHeight: 1.6,
  },
  '& blockquote': {
    borderLeft: `4px solid ${theme.palette.primary.main}`,
    paddingLeft: theme.spacing(2),
    marginLeft: 0,
    marginRight: 0,
    marginBottom: theme.spacing(2),
    backgroundColor: alpha(theme.palette.primary.main, 0.05),
    padding: theme.spacing(1, 2),
    borderRadius: theme.shape.borderRadius,
    '& p': {
      marginBottom: theme.spacing(1),
      fontStyle: 'italic',
      color: theme.palette.text.secondary,
    },
  },
  '& code': {
    backgroundColor: alpha(theme.palette.grey[500], 0.1),
    padding: theme.spacing(0.25, 0.5),
    borderRadius: theme.shape.borderRadius,
    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
    fontSize: '0.875em',
    color: theme.palette.text.primary,
  },
  '& pre': {
    backgroundColor: alpha(theme.palette.grey[900], 0.05),
    padding: theme.spacing(2),
    borderRadius: theme.shape.borderRadius,
    overflow: 'auto',
    marginBottom: theme.spacing(2),
    border: `1px solid ${alpha(theme.palette.grey[500], 0.2)}`,
    '& code': {
      backgroundColor: 'transparent',
      padding: 0,
      fontSize: '0.875rem',
    },
  },
  '& strong': {
    fontWeight: 600,
    color: theme.palette.text.primary,
  },
  '& em': {
    fontStyle: 'italic',
    color: theme.palette.text.secondary,
  },
  '& hr': {
    border: 'none',
    height: '1px',
    backgroundColor: theme.palette.divider,
    margin: theme.spacing(3, 0),
  },
  '& table': {
    width: '100%',
    borderCollapse: 'collapse',
    marginBottom: theme.spacing(2),
    border: `1px solid ${theme.palette.divider}`,
  },
  '& th, & td': {
    padding: theme.spacing(1, 2),
    textAlign: 'left',
    borderBottom: `1px solid ${theme.palette.divider}`,
    ...theme.typography.body2,
  },
  '& th': {
    backgroundColor: alpha(theme.palette.primary.main, 0.1),
    fontWeight: 600,
    color: theme.palette.text.primary,
  },
  '& a': {
    color: theme.palette.primary.main,
    textDecoration: 'none',
    '&:hover': {
      textDecoration: 'underline',
    },
  },
}));

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ 
  content, 
  variant = 'body1' 
}) => {
  const theme = useTheme();

  if (!content || content.trim() === '') {
    return (
      <Typography variant={variant} color="text.secondary">
        No content available.
      </Typography>
    );
  }

  return (
    <StyledMarkdownContainer>
      <ReactMarkdown
        components={{
          // Custom component for paragraphs to use Material-UI Typography
          p: ({ children }) => (
            <Typography variant={variant} component="p" sx={{ mb: 1.5, lineHeight: 1.7 }}>
              {children}
            </Typography>
          ),
          // Custom component for headings
          h1: ({ children }) => (
            <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2, fontWeight: 600 }}>
              {children}
            </Typography>
          ),
          h2: ({ children }) => (
            <Typography variant="h5" component="h2" sx={{ mt: 2.5, mb: 1.5, fontWeight: 600 }}>
              {children}
            </Typography>
          ),
          h3: ({ children }) => (
            <Typography variant="h6" component="h3" sx={{ mt: 2, mb: 1, fontWeight: 600 }}>
              {children}
            </Typography>
          ),
          // Custom component for horizontal rules
          hr: () => (
            <Divider sx={{ my: 3 }} />
          ),
          // Custom component for lists
          ul: ({ children }) => (
            <Box component="ul" sx={{ mb: 1.5, pl: 3 }}>
              {children}
            </Box>
          ),
          ol: ({ children }) => (
            <Box component="ol" sx={{ mb: 1.5, pl: 3 }}>
              {children}
            </Box>
          ),
          li: ({ children }) => (
            <Typography component="li" variant={variant} sx={{ mb: 0.5, lineHeight: 1.6 }}>
              {children}
            </Typography>
          ),
          // Custom component for blockquotes
          blockquote: ({ children }) => (
            <Box
              sx={{
                borderLeft: `4px solid ${theme.palette.primary.main}`,
                pl: 2,
                ml: 0,
                mr: 0,
                mb: 2,
                backgroundColor: alpha(theme.palette.primary.main, 0.05),
                p: 2,
                borderRadius: 1,
              }}
            >
              {children}
            </Box>
          ),
          // Custom component for code blocks
          code: ({ inline, children }) => {
            if (inline) {
              return (
                <Box
                  component="code"
                  sx={{
                    backgroundColor: alpha(theme.palette.grey[500], 0.1),
                    px: 0.5,
                    py: 0.25,
                    borderRadius: 0.5,
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    fontSize: '0.875em',
                  }}
                >
                  {children}
                </Box>
              );
            }
            return (
              <Box
                component="pre"
                sx={{
                  backgroundColor: alpha(theme.palette.grey[900], 0.05),
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  mb: 2,
                  border: `1px solid ${alpha(theme.palette.grey[500], 0.2)}`,
                }}
              >
                <Box
                  component="code"
                  sx={{
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    fontSize: '0.875rem',
                  }}
                >
                  {children}
                </Box>
              </Box>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </StyledMarkdownContainer>
  );
};

export default MarkdownRenderer;

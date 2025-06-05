import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Collapse,
  useTheme,
  alpha
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Source as SourceIcon
} from '@mui/icons-material';
import { documentService, SourceReference } from '../services/api';

// Utility function to format timestamps
const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });
};

interface ChatMessage {
  id: number;
  type: 'user' | 'assistant';
  content: string;
  sources?: SourceReference[];
  timestamp: string;
  isLoading?: boolean;
}

interface ChatInterfaceProps {
  documentId: string;
  documentName: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ documentId, documentName }) => {
  const theme = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversation history on mount
  useEffect(() => {
    loadConversationHistory();
  }, [documentId]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadConversationHistory = async () => {
    try {
      setLoadingHistory(true);
      const history = await documentService.getConversationHistory(documentId);
      
      // Convert API responses to chat messages
      const chatMessages: ChatMessage[] = [];
      history.forEach((qa) => {
        // Add user message
        chatMessages.push({
          id: qa.id * 2 - 1, // Ensure unique IDs
          type: 'user',
          content: qa.question_text,
          timestamp: qa.created_at
        });
        
        // Add assistant message
        chatMessages.push({
          id: qa.id * 2,
          type: 'assistant',
          content: qa.answer_text,
          sources: qa.sources,
          timestamp: qa.created_at
        });
      });
      
      setMessages(chatMessages);
    } catch (error) {
      console.error('Error loading conversation history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    const loadingMessage: ChatMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isLoading: true
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await documentService.askQuestion(documentId, userMessage.content);
      
      // Replace loading message with actual response
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessage.id 
          ? {
              ...msg,
              content: response.answer_text,
              sources: response.sources,
              isLoading: false
            }
          : msg
      ));
    } catch (error) {
      console.error('Error asking question:', error);
      // Replace loading message with error
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessage.id 
          ? {
              ...msg,
              content: 'Sorry, I encountered an error while processing your question. Please try again.',
              isLoading: false
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const toggleSources = (messageId: number) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  if (loadingHistory) {
    return (
      <Box 
        sx={{ 
          height: '600px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper 
        elevation={1} 
        sx={{ 
          p: 2, 
          borderRadius: '12px 12px 0 0',
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: 'white'
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Chat with {documentName}
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
          Ask questions about this document and get intelligent answers
        </Typography>
      </Paper>

      {/* Messages Area */}
      <Box 
        sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          backgroundColor: alpha(theme.palette.background.default, 0.5),
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            background: alpha(theme.palette.primary.main, 0.3),
            borderRadius: '3px',
          },
        }}
      >
        {messages.length === 0 ? (
          <Box 
            sx={{ 
              height: '100%', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexDirection: 'column',
              textAlign: 'center',
              color: 'text.secondary'
            }}
          >
            <BotIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
            <Typography variant="h6" gutterBottom>
              Start a conversation
            </Typography>
            <Typography variant="body2">
              Ask me anything about this document. I can help you understand the content, 
              find specific information, or answer questions about the data.
            </Typography>
          </Box>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onToggleSources={() => toggleSources(message.id)}
              sourcesExpanded={expandedSources.has(message.id)}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper 
        elevation={3}
        sx={{ 
          p: 2, 
          borderRadius: '0 0 12px 12px',
          borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask a question about this document..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '20px',
                backgroundColor: alpha(theme.palette.background.paper, 0.8),
                '&:hover': {
                  backgroundColor: theme.palette.background.paper,
                },
                '&.Mui-focused': {
                  backgroundColor: theme.palette.background.paper,
                }
              }
            }}
          />
          <IconButton
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            sx={{
              backgroundColor: theme.palette.primary.main,
              color: 'white',
              width: 48,
              height: 48,
              '&:hover': {
                backgroundColor: theme.palette.primary.dark,
              },
              '&.Mui-disabled': {
                backgroundColor: alpha(theme.palette.primary.main, 0.3),
                color: alpha(theme.palette.common.white, 0.5),
              }
            }}
          >
            {isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          </IconButton>
        </Box>
      </Paper>
    </Box>
  );
};

// Message Bubble Component
interface MessageBubbleProps {
  message: ChatMessage;
  onToggleSources: () => void;
  sourcesExpanded: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  onToggleSources, 
  sourcesExpanded 
}) => {
  const theme = useTheme();
  const isUser = message.type === 'user';

  return (
    <Box 
      sx={{ 
        mb: 3,
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        alignItems: 'flex-start',
        gap: 1
      }}
    >
      {!isUser && (
        <Avatar 
          sx={{ 
            bgcolor: theme.palette.primary.main,
            width: 32,
            height: 32,
            mt: 0.5
          }}
        >
          <BotIcon sx={{ fontSize: 18 }} />
        </Avatar>
      )}
      
      <Box sx={{ maxWidth: '75%', minWidth: '200px' }}>
        <Paper
          elevation={1}
          sx={{
            p: 2,
            borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
            backgroundColor: isUser 
              ? theme.palette.primary.main 
              : theme.palette.background.paper,
            color: isUser ? 'white' : 'text.primary',
            border: isUser ? 'none' : `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          }}
        >
          {message.isLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} color="inherit" />
              <Typography variant="body2">Thinking...</Typography>
            </Box>
          ) : (
            <Typography 
              variant="body1" 
              sx={{ 
                whiteSpace: 'pre-wrap',
                lineHeight: 1.5
              }}
            >
              {message.content}
            </Typography>
          )}
        </Paper>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && !message.isLoading && (
          <Box sx={{ mt: 1 }}>
            <Chip
              icon={<SourceIcon />}
              label={`${message.sources.length} source${message.sources.length > 1 ? 's' : ''}`}
              size="small"
              onClick={onToggleSources}
              onDelete={onToggleSources}
              deleteIcon={sourcesExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              sx={{ 
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                color: theme.palette.primary.main,
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.2),
                }
              }}
            />
            
            <Collapse in={sourcesExpanded}>
              <Paper 
                variant="outlined" 
                sx={{ 
                  mt: 1, 
                  maxHeight: '200px', 
                  overflow: 'auto',
                  backgroundColor: alpha(theme.palette.background.default, 0.5)
                }}
              >
                <List dense>
                  {message.sources.map((source, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemText
                          primary={source.snippet}
                          secondary={source.page ? `Page ${source.page}` : undefined}
                          primaryTypographyProps={{
                            variant: 'body2',
                            sx: { fontStyle: 'italic' }
                          }}
                          secondaryTypographyProps={{
                            variant: 'caption',
                            color: 'primary'
                          }}
                        />
                      </ListItem>
                      {index < message.sources!.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </Paper>
            </Collapse>
          </Box>
        )}

        {/* Timestamp */}
        <Typography 
          variant="caption" 
          sx={{ 
            display: 'block',
            textAlign: isUser ? 'right' : 'left',
            mt: 0.5,
            opacity: 0.7,
            color: isUser ? 'rgba(255,255,255,0.7)' : 'text.secondary'
          }}
        >
          {formatTimestamp(message.timestamp)}
        </Typography>
      </Box>

      {isUser && (
        <Avatar 
          sx={{ 
            bgcolor: theme.palette.secondary.main,
            width: 32,
            height: 32,
            mt: 0.5
          }}
        >
          <PersonIcon sx={{ fontSize: 18 }} />
        </Avatar>
      )}
    </Box>
  );
};

export default ChatInterface;

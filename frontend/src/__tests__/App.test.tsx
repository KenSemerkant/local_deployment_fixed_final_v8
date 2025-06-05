import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock the AuthContext
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: false,
    isLoading: false,
  }),
  AuthProvider: ({ children }) => <div>{children}</div>,
}));

// Mock the react-router-dom
jest.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }) => <div>{children}</div>,
  Routes: ({ children }) => <div>{children}</div>,
  Route: () => <div>Route</div>,
  Navigate: () => <div>Navigate</div>,
  useNavigate: () => jest.fn(),
}));

test('renders without crashing', () => {
  render(<App />);
  // Basic test to ensure the app renders without crashing
  expect(screen.getByText(/AI Financial Analyst/i)).toBeInTheDocument();
});

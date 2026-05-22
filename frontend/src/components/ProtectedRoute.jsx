import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { hasPermission } from '../utils/roleUtils';
import UnauthorizedAccess from './UnauthorizedAccess';

// Create a simple auth context for demonstration
const AuthContext = React.createContext({
  user: null,
  setUser: () => {}
});

const ProtectedRoute = ({ children, permission }) => {
  const { user } = useContext(AuthContext);
  
  // If not authenticated, redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  // If authenticated but doesn't have required permission
  if (permission && !hasPermission(user, permission)) {
    return <UnauthorizedAccess component={children.type?.name || 'Protected Resource'} />;
  }
  
  // If authenticated and has permission, render the component
  return children;
};

export default ProtectedRoute;
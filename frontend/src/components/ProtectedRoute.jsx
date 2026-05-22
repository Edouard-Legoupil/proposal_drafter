import React from 'react';
import { Navigate } from 'react-router-dom';
import { hasPermission } from '../utils/roleUtils';
import { useSelector } from 'react-redux';
import UnauthorizedAccess from './UnauthorizedAccess';

const ProtectedRoute = ({ children, permission }) => {
  const user = useSelector(state => state.auth.user);
  
  // If not authenticated, redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  // If authenticated but doesn't have required permission
  if (permission && !hasPermission(permission)) {
    return <UnauthorizedAccess component={children.type?.name || 'Protected Resource'} />;
  }
  
  // If authenticated and has permission, render the component
  return children;
};

export default ProtectedRoute;
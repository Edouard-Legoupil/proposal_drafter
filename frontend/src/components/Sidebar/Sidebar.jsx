import React, { useContext } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { List, ListItem, ListItemIcon, ListItemText, Divider, Box, Tooltip } from '@mui/material';
import { Dashboard, Analytics, Description, Assessment, BugReport, Groups, Lock } from '@mui/icons-material';
import { hasPermission, getUIConfiguration } from '../../utils/roleUtils';

// Create a simple auth context for demonstration
// In a real app, this would come from your actual auth system
const AuthContext = React.createContext({
  user: null,
  setUser: () => {}
});

const Sidebar = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // Sidebar items configuration with role requirements
  const sidebarItems = [
    {
      text: 'Dashboard',
      icon: <Dashboard />,
      path: '/dashboard',
      permission: null // Always visible
    },
    {
      text: 'Proposals',
      icon: <Description />,
      path: '/proposals',
      permission: null // Always visible
    },
    {
      text: 'Knowledge Cards',
      icon: <Assessment />,
      path: '/knowledge-cards',
      permission: null // Always visible
    },
    {
      text: 'Metrics Dashboard',
      icon: <Analytics />,
      path: '/dashboard/metrics',
      permission: 'access_metrics'
    },
    {
      text: 'Donor Templates',
      icon: <Description />,
      path: '/templates',
      permission: 'access_template'
    },
    {
      text: 'Quality Gate',
      icon: <BugReport />,
      path: '/quality-gate',
      permission: 'access_quality_gate'
    },
    {
      text: 'Incident Analysis',
      icon: <BugReport />,
      path: '/incidents',
      permission: 'access_incident'
    }
  ];
  
  // Filter items based on permissions
  const visibleItems = sidebarItems.filter(item => {
    return !item.permission || hasPermission(item.permission);
  });
  
  const handleNavigation = (path, permission) => {
    if (permission && !hasPermission(permission)) {
      // Prevent navigation and show unauthorized
      navigate('/unauthorized');
      return false;
    }
    return true;
  };
  
  return (
    <Box sx={{ width: 250, height: '100vh', backgroundColor: '#f5f5f5' }}>
      <List>
        {visibleItems.map((item, index) => (
          <React.Fragment key={index}>
            <ListItem
              button
              component={NavLink}
              to={item.path}
              exact={item.exact}
              activeStyle={{ backgroundColor: 'rgba(0, 0, 0, 0.08)' }}
              onClick={(e) => {
                if (item.permission && !hasPermission(item.permission)) {
                  e.preventDefault();
                  handleNavigation(item.path, item.permission);
                }
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
            
            {/* Add dividers between sections */}
            {index === 2 && <Divider sx={{ my: 1 }} />}
          </React.Fragment>
        ))}
      </List>
    </Box>
  );
};

export default Sidebar;
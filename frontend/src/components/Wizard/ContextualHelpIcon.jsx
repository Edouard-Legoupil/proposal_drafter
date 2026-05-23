/**
 * Contextual Help Icon Component
 * 
 * Help icon that can be placed next to specific features to provide
 * context-sensitive help when clicked
 */

import React from 'react';
import { useWizard } from '../../context/WizardContext';
import { IconButton, Tooltip } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const ContextualHelpIcon = ({ topic = null }) => {
    const { setIsOpen, setSelectedCategory } = useWizard();
    
    const handleClick = () => {
        setIsOpen(true);
        if (topic) {
            // Map topic to category - this would be enhanced with actual topic-category mapping
            setSelectedCategory(topic);
        }
    };
    
    return (
        <Tooltip title="Get help on this topic" arrow>
            <IconButton
                onClick={handleClick}
                size="small"
                color="primary"
                sx={{ ml: 1 }}
                aria-label={`Get help on ${topic || 'this topic'}`}
            >
                <HelpOutlineIcon fontSize="small" />
            </IconButton>
        </Tooltip>
    );
};

export default ContextualHelpIcon;
/**
 * Wizard Button Component
 *
 * Main help button that appears in the navigation to open the wizard modal
 */

import React from 'react';
import { useWizard } from '../../context/WizardContext';
import { Button, Tooltip } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const WizardButton = () => {
    const { setIsOpen } = useWizard();

    const handleClick = () => {
        setIsOpen(true);
    };

    return (
        <Tooltip title="Help & Support" arrow>
            <Button
                variant="contained"
                color="primary"
                onClick={handleClick}
                startIcon={<HelpOutlineIcon />}
                sx={{ ml: 2 }}
                aria-label="Open help wizard"
                data-testid="wizard-help-button"
            >
                Help
            </Button>
        </Tooltip>
    );
};

export default WizardButton;

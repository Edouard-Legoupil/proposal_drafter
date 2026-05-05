import React from 'react';
import PropTypes from 'prop-types';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography } from '@mui/material';
import './AnalysisModal.css';

export default function AnalysisModal({ open, onClose, analysis }) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>AI Analysis Details</DialogTitle>
      <DialogContent dividers>
        <div className="analysis-modal-content">
          {Object.entries(analysis || {}).map(([key, value]) => (
            <div className="analysis-modal-section" key={key}>
              <Typography variant="subtitle2" className="analysis-modal-key">
                {key}
              </Typography>
              {value !== null && typeof value === 'object' ? (
                <pre className="analysis-modal-value">
                  {JSON.stringify(value, null, 2)}
                </pre>
              ) : (
                <Typography variant="body2" className="analysis-modal-value">
                  {String(value)}
                </Typography>
              )}
            </div>
          ))}
        </div>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">Close</Button>
      </DialogActions>
    </Dialog>
  );
}

AnalysisModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  analysis: PropTypes.object,
};

AnalysisModal.defaultProps = {
  analysis: {},
};

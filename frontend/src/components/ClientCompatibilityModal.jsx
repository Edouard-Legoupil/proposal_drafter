import { Modal, Box, Typography, Button, Divider } from '@mui/material';

export function ClientCompatibilityModal({ open, onClose, clientInfo }) {
  if (!open) return null;

  const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 500,
    bgcolor: 'background.paper',
    boxShadow: 24,
    p: 4,
    borderRadius: 2,
    outline: 'none'
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="compatibility-modal-title"
      aria-describedby="compatibility-modal-description"
    >
      <Box sx={modalStyle}>
        <Typography id="compatibility-modal-title" variant="h6" gutterBottom>
          🚨 Unsupported Browser/OS Detected
        </Typography>

        <Typography id="compatibility-modal-description" variant="body1" paragraph>
          For the best experience, we recommend:
        </Typography>

        <Typography variant="body2" paragraph>
          <strong>Supported OS:</strong> Windows 11+ or macOS 12+
        </Typography>

        <Typography variant="body2" paragraph>
          <strong>Supported Browsers:</strong> Chrome 110+, Firefox 110+, Edge 110+, Safari 15+
        </Typography>

        <Divider sx={{ my: 2 }} />

        {clientInfo && (
          <Typography variant="body2" paragraph>
            <strong>Your System:</strong> {clientInfo.os.name} {clientInfo.os.version} • {clientInfo.browser.name} {clientInfo.browser.version}
          </Typography>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
          <Button variant="outlined" onClick={onClose}>
            Continue Anyway
          </Button>
          <Button variant="contained" color="primary">
            Learn More
          </Button>
        </Box>
      </Box>
    </Modal>
  );
}

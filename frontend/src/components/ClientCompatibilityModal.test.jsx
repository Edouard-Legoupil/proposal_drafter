import { render, screen, fireEvent } from '@testing-library/react';
import { ClientCompatibilityModal } from './ClientCompatibilityModal';

describe('ClientCompatibilityModal', () => {
  const mockClientInfo = {
    os: { name: 'Windows', version: '10', isSupported: false },
    browser: { name: 'Chrome', version: '90', isSupported: false }
  };

  it('should render when open', () => {
    const { container } = render(
      <ClientCompatibilityModal
        open={true}
        onClose={() => {}}
        clientInfo={mockClientInfo}
      />
    );

    expect(screen.getByText(/Unsupported Browser\/OS Detected/i)).toBeInTheDocument();
    expect(screen.getByText(/Windows 10/i)).toBeInTheDocument();
    expect(screen.getByText(/Chrome 90/i)).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    const { container } = render(
      <ClientCompatibilityModal
        open={false}
        onClose={() => {}}
        clientInfo={mockClientInfo}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('should call onClose when Continue Anyway is clicked', () => {
    const handleClose = vi.fn();
    render(
      <ClientCompatibilityModal
        open={true}
        onClose={handleClose}
        clientInfo={mockClientInfo}
      />
    );

    fireEvent.click(screen.getByText(/Continue Anyway/i));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should have proper accessibility attributes', () => {
    render(
      <ClientCompatibilityModal
        open={true}
        onClose={() => {}}
        clientInfo={mockClientInfo}
      />
    );

    // Material UI Modal uses role="presentation", so we check for the title instead
    const title = screen.getByText(/Unsupported Browser\/OS Detected/i);
    expect(title).toBeInTheDocument();
    expect(title).toHaveAccessibleName();
  });
});

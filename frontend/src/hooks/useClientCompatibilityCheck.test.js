import { renderHook, act } from '@testing-library/react';
import { useClientCompatibilityCheck } from './useClientCompatibilityCheck';
import { detectClientInfo } from '../utils/clientDetection';

// Mock the client detection
vi.mock('../utils/clientDetection', () => ({
  detectClientInfo: vi.fn()
}));

describe('useClientCompatibilityCheck', () => {
  beforeEach(() => {
    detectClientInfo.mockClear();
  });

  it('should show warning for incompatible client', () => {
    detectClientInfo.mockReturnValue({
      isCompatible: false,
      os: { name: 'Windows', version: '10', isSupported: false },
      browser: { name: 'Chrome', version: '90', isSupported: false }
    });

    const { result } = renderHook(() => useClientCompatibilityCheck());

    expect(result.current.showWarning).toBe(true);
    expect(result.current.isCompatible).toBe(false);
  });

  it('should not show warning for compatible client', () => {
    detectClientInfo.mockReturnValue({
      isCompatible: true,
      os: { name: 'Windows', version: '11', isSupported: true },
      browser: { name: 'Chrome', version: '110', isSupported: true }
    });

    const { result } = renderHook(() => useClientCompatibilityCheck());

    expect(result.current.showWarning).toBe(false);
    expect(result.current.isCompatible).toBe(true);
  });

  it('should allow dismissing warning', () => {
    detectClientInfo.mockReturnValue({
      isCompatible: false,
      os: { name: 'Windows', version: '10', isSupported: false },
      browser: { name: 'Chrome', version: '90', isSupported: false }
    });

    const { result } = renderHook(() => useClientCompatibilityCheck());

    act(() => {
      result.current.dismissWarning();
    });

    expect(result.current.showWarning).toBe(false);
  });
});

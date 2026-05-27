import { useState, useEffect, useMemo } from 'react';
import { detectClientInfo } from '../utils/clientDetection';

export function useClientCompatibilityCheck() {
  const [clientInfo, setClientInfo] = useState(null);
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    const checkCompatibility = () => {
      try {
        const info = detectClientInfo();
        setClientInfo(info);

        if (!info.isCompatible) {
          setShowWarning(true);
        }
      } catch (error) {
        console.error('Client compatibility check failed:', error);
        // Fail gracefully - don't show warning on error
      }
    };

    checkCompatibility();
  }, []);

  const dismissWarning = () => setShowWarning(false);

  const memoizedValue = useMemo(() => ({
    clientInfo,
    showWarning,
    dismissWarning,
    isCompatible: clientInfo?.isCompatible ?? true
  }), [clientInfo, showWarning]);

  return memoizedValue;
}

import { describe, it, expect } from 'vitest';
import { detectClientInfo, detectOS, detectBrowser } from './clientDetection';

describe('clientDetection', () => {
  it('should detect Windows 11', () => {
    const windows11UserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36';
    const os = detectOS(windows11UserAgent);
    expect(os.name).toBe('Windows');
    expect(os.version).toBe('11');
    expect(os.isSupported).toBe(true);
  });

  it('should detect macOS 12', () => {
    const macOS12UserAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/537.36';
    const os = detectOS(macOS12UserAgent);
    expect(os.name).toBe('macOS');
    expect(os.version).toBe('12');
    expect(os.isSupported).toBe(true);
  });

  it('should detect Chrome 110', () => {
    const chrome110UserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36';
    const browser = detectBrowser(chrome110UserAgent);
    expect(browser.name).toBe('Chrome');
    expect(browser.version).toBe('110');
    expect(browser.isSupported).toBe(true);
  });

  it('should detect unsupported browser', () => {
    const oldChromeUserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.36';
    const browser = detectBrowser(oldChromeUserAgent);
    expect(browser.name).toBe('Chrome');
    expect(browser.version).toBe('90');
    expect(browser.isSupported).toBe(false);
  });

  it('should handle full client detection', () => {
    const userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36';
    const clientInfo = detectClientInfo(userAgent);
    expect(clientInfo.os.isSupported).toBe(true);
    expect(clientInfo.browser.isSupported).toBe(true);
    expect(clientInfo.isCompatible).toBe(true);
  });
});

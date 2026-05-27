// Minimum baseline configuration
const MIN_OS_VERSIONS = {
  Windows: '11',
  macOS: '12'
};

const MIN_BROWSER_VERSIONS = {
  Chrome: '110',
  Firefox: '110',
  Edge: '110',
  Safari: '15'
};

export function detectOS(userAgent) {
  if (!userAgent) {
    return { name: 'Unknown', version: 'Unknown', isSupported: true };
  }

  let name = 'Unknown';
  let version = 'Unknown';
  let isSupported = false;

  // Windows detection
  if (userAgent.includes('Windows NT 10.0')) {
    name = 'Windows';
    version = '11'; // Windows 10.0 is actually Windows 11
    isSupported = parseFloat(version) >= parseFloat(MIN_OS_VERSIONS.Windows);
  } else if (userAgent.includes('Windows NT 6.3')) {
    name = 'Windows';
    version = '8.1';
    isSupported = false;
  } else if (userAgent.includes('Mac OS X')) {
    name = 'macOS';
    const macVersionMatch = userAgent.match(/Mac OS X (\d+_[\d_]+)/);
    if (macVersionMatch) {
      version = macVersionMatch[1].replace('_', '.').split('.')[0]; // Get major version only
      isSupported = parseFloat(version) >= parseFloat(MIN_OS_VERSIONS.macOS);
    }
  }

  return { name, version, isSupported };
}

export function detectBrowser(userAgent) {
  if (!userAgent) {
    return { name: 'Unknown', version: 'Unknown', isSupported: true };
  }

  let name = 'Unknown';
  let version = 'Unknown';
  let isSupported = false;

  // Chrome detection
  if (userAgent.includes('Chrome') && !userAgent.includes('Edge')) {
    name = 'Chrome';
    const versionMatch = userAgent.match(/Chrome\/(\d+)/);
    if (versionMatch) {
      version = versionMatch[1];
      isSupported = parseFloat(version) >= parseFloat(MIN_BROWSER_VERSIONS.Chrome);
    }
  }
  // Firefox detection
  else if (userAgent.includes('Firefox')) {
    name = 'Firefox';
    const versionMatch = userAgent.match(/Firefox\/(\d+)/);
    if (versionMatch) {
      version = versionMatch[1];
      isSupported = parseFloat(version) >= parseFloat(MIN_BROWSER_VERSIONS.Firefox);
    }
  }
  // Edge detection
  else if (userAgent.includes('Edg')) {
    name = 'Edge';
    const versionMatch = userAgent.match(/Edg\/(\d+)/);
    if (versionMatch) {
      version = versionMatch[1];
      isSupported = parseFloat(version) >= parseFloat(MIN_BROWSER_VERSIONS.Edge);
    }
  }
  // Safari detection
  else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
    name = 'Safari';
    const versionMatch = userAgent.match(/Version\/(\d+)/);
    if (versionMatch) {
      version = versionMatch[1];
      isSupported = parseFloat(version) >= parseFloat(MIN_BROWSER_VERSIONS.Safari);
    }
  }

  return { name, version, isSupported };
}

export function detectClientInfo(userAgent = navigator.userAgent) {
  try {
    const os = detectOS(userAgent);
    const browser = detectBrowser(userAgent);

    return {
      os,
      browser,
      isCompatible: os.isSupported && browser.isSupported,
      userAgent
    };
  } catch (error) {
    console.error('Client detection failed:', error);
    // Fail gracefully - assume compatible
    return {
      os: { name: 'Unknown', version: 'Unknown', isSupported: true },
      browser: { name: 'Unknown', version: 'Unknown', isSupported: true },
      isCompatible: true,
      userAgent: ''
    };
  }
}

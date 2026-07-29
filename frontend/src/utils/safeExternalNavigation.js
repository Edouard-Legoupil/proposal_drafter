export function openSafeExternalUrl(rawUrl, openWindow = window.open.bind(window)) {
  try {
    const url = new URL(rawUrl)
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
      return false
    }
    openWindow(url.href, '_blank', 'noopener,noreferrer')
    return true
  } catch {
    return false
  }
}

import React from 'react'

/**
 * Displays an error message in a consistent banner.
 */
export default function ErrorBanner({ message }) {
  return <div className="panel-error">{message}</div>
}

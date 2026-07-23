import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ErrorBanner from './ErrorBanner'

describe('ErrorBanner', () => {
  it('displays the error message inside a panel-error div', () => {
    const msg = 'Test error occurred'
    render(<ErrorBanner message={msg} />)
    const el = screen.getByText(msg)
    expect(el).toBeInTheDocument()
    expect(el).toHaveClass('panel-error')
  })
})

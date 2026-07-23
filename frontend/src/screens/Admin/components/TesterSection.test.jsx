import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import TesterSection from './TesterSection'

describe('TesterSection', () => {
  const props = {
    tester: { subjectType: 'user', subjectId: '', operation: 'op1' },
    setTester: vi.fn(),
    testerResult: { allowed: true, reason: 'ok', source: 'src' },
    statusMessage: 'test-msg',
    actionLoading: false,
    onTest: vi.fn(),
    operationOptions: [{ value: 'op1', label: 'Op1' }],
    users: [],
    options: {}
  }

  it('renders statusMessage and result', () => {
    render(<TesterSection {...props} />)
    expect(screen.getByText(/test-msg/i)).toBeInTheDocument()
    expect(screen.getByText(/✅ Allowed/i)).toBeInTheDocument()
    expect(screen.getByText(/Source: src/)).toBeInTheDocument()
  })

  it('calls onTest when submit is clicked', () => {
    render(<TesterSection {...props} />)
    fireEvent.click(screen.getByRole('button', { name: /run test/i }))
    expect(props.onTest).toHaveBeenCalled()
  })
})

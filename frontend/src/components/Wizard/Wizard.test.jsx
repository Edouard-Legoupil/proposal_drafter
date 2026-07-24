import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { delay, http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { WizardProvider, useWizard } from '../../context/WizardContext'
import { server } from '../../mocks/server'
import ContextualHelpIcon from './ContextualHelpIcon'
import WizardButton from './WizardButton'
import WizardModal from './WizardModal'

function renderWizard() {
  return render(
    <WizardProvider>
      <WizardButton />
      <WizardModal />
    </WizardProvider>
  )
}

async function openWizard() {
  fireEvent.click(screen.getByRole('button', { name: /open help wizard/i }))
  return screen.findByRole('dialog')
}

describe('WizardButton', () => {
  it('renders an accessible help button', () => {
    render(<WizardProvider><WizardButton /></WizardProvider>)
    expect(screen.getByRole('button', { name: /open help wizard/i })).toHaveTextContent('Help')
  })

  it('opens the help dialog', async () => {
    renderWizard()
    await openWizard()
    expect(screen.getByText('Proposal Drafter Help')).toBeInTheDocument()
  })
})

describe('ContextualHelpIcon', () => {
  it('opens contextual help and stores its topic', () => {
    function TopicProbe() {
      const { selectedCategory } = useWizard()
      return <span>{selectedCategory || 'none'}</span>
    }

    render(
      <WizardProvider>
        <ContextualHelpIcon topic="proposal-writing" />
        <TopicProbe />
      </WizardProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: /get help on proposal-writing/i }))
    expect(screen.getByText('proposal-writing')).toBeInTheDocument()
  })
})

describe('WizardModal', () => {
  it('does not render dialog content while closed', () => {
    render(<WizardProvider><WizardModal /></WizardProvider>)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows loading feedback while initial data is pending', async () => {
    server.use(
      http.get('/api/wizard/categories', async () => {
        await delay(100)
        return HttpResponse.json([])
      })
    )
    renderWizard()
    await openWizard()
    expect(screen.getByLabelText('Loading questions')).toBeInTheDocument()
    expect(await screen.findByText('General')).toBeInTheDocument()
  })

  it('displays fallback categories when the API has no content', async () => {
    renderWizard()
    await openWizard()
    expect(await screen.findByText('General')).toBeInTheDocument()
    expect(screen.getByText('Proposal Creation')).toBeInTheDocument()
    expect(screen.getAllByText('5')).toHaveLength(2)
  })

  it('displays popular questions', async () => {
    renderWizard()
    await openWizard()
    fireEvent.click(await screen.findByRole('tab', { name: /popular questions/i }))
    expect(await screen.findByText(/How do I create a new proposal/i)).toBeInTheDocument()
    expect(screen.getByText('Viewed 120 times')).toBeInTheDocument()
  })

  it('searches fallback help content', async () => {
    renderWizard()
    await openWizard()
    const search = screen.getByPlaceholderText('Search help topics...')
    fireEvent.change(search, { target: { value: 'AI-generated' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(await screen.findByText(/Can I edit the AI-generated proposal/i)).toBeInTheDocument()
  })

  it('opens a question and submits feedback', async () => {
    renderWizard()
    await openWizard()
    fireEvent.click(await screen.findByRole('button', { name: /select category proposal creation/i }))
    fireEvent.click(await screen.findByRole('button', { name: /view answer to how do i create a new proposal/i }))
    expect(await screen.findByText(/Navigate to the Dashboard/i)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('5 Stars'))
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }))
    await waitFor(() => expect(screen.getByText('Rate this answer')).toBeInTheDocument())
  })

  it('exposes navigation and search controls to assistive technology', async () => {
    renderWizard()
    await openWizard()
    expect(screen.getByRole('tablist', { name: /wizard tabs/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Search help topics...')).toBeInTheDocument()
  })
})

describe('WizardContext', () => {
  it('throws when consumed outside its provider', () => {
    function Probe() {
      useWizard()
      return null
    }
    expect(() => render(<Probe />)).toThrow('useWizard must be used within a WizardProvider')
  })

  it('provides a closed, ready initial state', () => {
    function Probe() {
      const context = useWizard()
      return <span>{context.isOpen ? 'open' : 'closed'}-{context.loading ? 'loading' : 'ready'}</span>
    }
    render(<WizardProvider><Probe /></WizardProvider>)
    expect(screen.getByText('closed-ready')).toBeInTheDocument()
  })
})

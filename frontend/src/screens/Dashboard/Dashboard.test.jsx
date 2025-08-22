import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from './Dashboard'
import { server } from '../../mocks/server'

// Mock the navigate function
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    }
})

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('Dashboard Component', () => {
    it('renders the main tabs', async () => {
        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        )

        await waitFor(() => {
            expect(screen.getByRole('tab', { name: /my proposals/i })).toBeInTheDocument()
            expect(screen.getByRole('tab', { name: /knowledge library/i })).toBeInTheDocument()
            expect(screen.getByRole('tab', { name: /pending reviews/i })).toBeInTheDocument()
        })
    })

    it('displays proposals in the "My Proposals" tab', async () => {
        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        )
        await waitFor(async () => {
            expect(await screen.findByText('First Project')).toBeInTheDocument()
            expect(await screen.findByText('Second Project')).toBeInTheDocument()
        })
    })

    it('displays knowledge cards in the "Knowledge Library" tab', async () => {
        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        )
        await userEvent.click(screen.getByRole('tab', { name: /knowledge library/i }))
        await waitFor(async () => {
            expect(await screen.findByText('ECHO')).toBeInTheDocument()
            expect(await screen.findByText('Country A')).toBeInTheDocument()
        })
    })

    it('displays reviews in the "Pending Reviews" tab', async () => {
        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        )
        await userEvent.click(screen.getByRole('tab', { name: /pending reviews/i }))
        await waitFor(async () => {
            expect(await screen.findByText('Review Project 1')).toBeInTheDocument()
        })
    })

    it('opens the new proposal modal when "Start New Proposal" is clicked', async () => {
        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        )
        const newProposalButton = await screen.findByRole('button', { name: /start new proposal/i })
        await userEvent.click(newProposalButton)
        await waitFor(async () => {
            expect(await screen.findByRole('dialog', { name: /start new proposal/i })).toBeInTheDocument()
        })
    })

    it('shows a "Submit for Review" button for draft proposals', async () => {
        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        )
        await waitFor(async () => {
            const reviewButtons = await screen.findAllByRole('button', { name: /submit for review/i })
            expect(reviewButtons.length).toBeGreaterThan(0)
        })
    })
})

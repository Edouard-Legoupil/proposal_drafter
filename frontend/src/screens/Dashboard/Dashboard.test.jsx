import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from './Dashboard'
import { server } from '../../mocks/server'
import { http, HttpResponse } from 'msw'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom')
        return {
                ...actual,
                useNavigate: () => mockNavigate,
        }
})

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

describe('Dashboard Component', () => {
        beforeEach(() => {
                sessionStorage.clear()
                mockNavigate.mockClear()
        })

        const drafts = [
                { proposal_id: '1', project_title: 'First Project', summary: 'Sum1', updated_at: '2025-05-10T10:00:00.123Z', is_accepted: true },
                { proposal_id: '2', project_title: 'Second Project', summary: 'Sum2', updated_at: '2025-05-11T11:30:00.456Z', is_accepted: false },
        ]
        const reviews = [
                { proposal_id: '1', project_title: 'First Project', summary: 'Sum1', updated_at: '2025-05-10T10:00:00.123Z', is_accepted: true }
        ]

        it('renders list of drafts after fetch', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                server.use(http.get(`${API_BASE_URL}/proposals/reviews`, () => HttpResponse.json({ reviews })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )
                const proposalsPanel = await screen.findByTestId('proposals-panel')

                await waitFor(() => {
                        expect(within(proposalsPanel).getByText(/first project/i)).toBeInTheDocument()
                        expect(within(proposalsPanel).getByText(/second project/i)).toBeInTheDocument()
                })
        })

        it('filters drafts based on search term', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                server.use(http.get(`${API_BASE_URL}/proposals/reviews`, () => HttpResponse.json({ reviews })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )
                const proposalsPanel = await screen.findByTestId('proposals-panel')

                await waitFor(() => {
                        expect(within(proposalsPanel).getByText('First Project')).toBeInTheDocument()
                        expect(within(proposalsPanel).getByText('Second Project')).toBeInTheDocument()
                })

                const searchInput = screen.getByPlaceholderText(/search/i)
                await userEvent.clear(searchInput)
                await userEvent.type(searchInput, 'second')


                await waitFor(() => {
                        expect(within(proposalsPanel).queryByText('First Project')).not.toBeInTheDocument()
                })

                expect(within(proposalsPanel).getByText('Second Project')).toBeInTheDocument()
        })

        it('shows "Start New Proposal" button when no drafts are returned', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts: [] })))
                server.use(http.get(`${API_BASE_URL}/proposals/reviews`, () => HttpResponse.json({ reviews })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )
                const proposalsPanel = await screen.findByTestId('proposals-panel')

                await waitFor(() => {
                        expect(within(proposalsPanel).getByText(/Start New Proposal/i)).toBeInTheDocument()
                })
        })

        it('navigates to /chat on "Start New Proposal" click', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts: [] })))
                server.use(http.get(`${API_BASE_URL}/proposals/reviews`, () => HttpResponse.json({ reviews })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                const proposalsPanel = await screen.findByTestId('proposals-panel')
                const createBtn = await within(proposalsPanel).findByTestId('new-proposal-button')
                await userEvent.click(createBtn)

                await waitFor(() => {
                        expect(mockNavigate).toHaveBeenCalledWith('/chat')
                })
        })

        it('clicking project sets sessionStorage and navigates', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                server.use(http.get(`${API_BASE_URL}/proposals/reviews`, () => HttpResponse.json({ reviews })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                const proposalsPanel = await screen.findByTestId('proposals-panel')
                const projectItem = await within(proposalsPanel).findByText('First Project')

                await userEvent.click(projectItem)

                await waitFor(() => {
                        expect(sessionStorage.getItem('proposal_id')).toBe('1')
                        expect(mockNavigate).toHaveBeenCalledWith('/chat/1')
                })
        })

        it('shows a "Shared" badge on accepted projects and "Draft" on others', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                server.use(http.get(`${API_BASE_URL}/proposals/reviews`, () => HttpResponse.json({ reviews })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                const proposalsPanel = await screen.findByTestId('proposals-panel')
                // Find the container for the first project to scope the search for the badge
                const firstProjectContainer = await within(proposalsPanel).findByText('First Project')
                // Check for the "Shared" badge within the context of the first project's container/card
                expect(within(firstProjectContainer.closest('.Dashboard_project')).getByText(/Shared/i)).toBeInTheDocument()

                // Find the container for the second project
                const secondProjectContainer = await within(proposalsPanel).findByText('Second Project')
                // Check for the "Draft" badge within the context of the second project's container/card
                expect(within(secondProjectContainer.closest('.Dashboard_project')).getByText(/Draft/i)).toBeInTheDocument()
        })
})

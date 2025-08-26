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

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

describe('Dashboard Component', () => {
        beforeEach(() => {
                sessionStorage.clear()
                mockNavigate.mockClear()
        })

        const drafts = [
                { proposal_id: '1', project_title: 'First Project', summary: 'Sum1', updated_at: '2025-05-10T10:00:00.123Z', is_accepted: true },
                { proposal_id: '2', project_title: 'Second Project', summary: 'Sum2', updated_at: '2025-05-11T11:30:00.456Z', is_accepted: false },
        ]

        it('renders list of drafts after fetch', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                await waitFor(() => {
                        expect(screen.getByText(/first project/i)).toBeInTheDocument()
                        expect(screen.getByText(/second project/i)).toBeInTheDocument()
                })
        })

        it('filters drafts based on search term', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                await waitFor(() => {
                        expect(screen.getByText('First Project')).toBeInTheDocument()
                        expect(screen.getByText('Second Project')).toBeInTheDocument()
                })

                const searchInput = screen.getByPlaceholderText(/search/i)
                await userEvent.clear(searchInput)
                await userEvent.type(searchInput, 'second')


                await waitFor(() => {
                        expect(screen.queryByText('First Project')).not.toBeInTheDocument()
                })

                expect(screen.getByText('Second Project')).toBeInTheDocument()
        })

        it('shows "Sample proposals" heading when no drafts are returned', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts: [] })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                await waitFor(() => {
                        expect(screen.getByText(/Sample proposals/i)).toBeInTheDocument()
                })
        })

        it('navigates to /chat on "Generate New Proposal" click', async () => {
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                const createBtn = await screen.findByRole('button', { name: /Generate New Proposal/i })
                await userEvent.click(createBtn)

                await waitFor(() => {
                        expect(mockNavigate).toHaveBeenCalledWith('/chat')
                })
        })

        it('clicking project sets sessionStorage and navigates', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                const projectItem = await screen.findByText('First Project')

                await userEvent.click(projectItem)

                await waitFor(() => {
                        expect(sessionStorage.getItem('proposal_id')).toBe('1')
                        expect(mockNavigate).toHaveBeenCalledWith('/chat')
                })
        }),

        it('shows a "Shared" badge on accepted projects and "Draft" on others', async () => {
                server.use(http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts })))
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                // Find the container for the first project to scope the search for the badge
                const firstProjectContainer = await screen.findByText('First Project')
                // Check for the "Shared" badge within the context of the first project's container/card
                expect(within(firstProjectContainer.closest('.Dashboard_project')).getByText(/Shared/i)).toBeInTheDocument()

                // Find the container for the second project
                const secondProjectContainer = await screen.findByText('Second Project')
                // Check for the "Draft" badge within the context of the second project's container/card
                expect(within(secondProjectContainer.closest('.Dashboard_project')).getByText(/Draft/i)).toBeInTheDocument()
        })
})

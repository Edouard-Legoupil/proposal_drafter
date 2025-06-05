import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
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

        beforeAll(() => {
                server.use(
                        http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts }))
                )
        })

        it('renders list of drafts after fetch', async () => {
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

        it('shows no drafts notice when no drafts returned', async () => {
                server.use(
                        http.get(`${API_BASE_URL}/list-drafts`, () => HttpResponse.json({ drafts: [] }))
                )

                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                await waitFor(() => {
                        expect(screen.getByText(/no drafts found\./i)).toBeInTheDocument()
                })
        })

        it('navigates to /chat on create new click', async () => {
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                const createBtn = await screen.findByRole('button', { name: /create new proposal/i })
                await userEvent.click(createBtn)
                await waitFor(() => {
                        expect(mockNavigate).toHaveBeenCalledWith('/chat')
                })
        })

        it('clicking project sets sessionStorage and navigates', async () => {
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

        it('shows an Approved badge on accepted projects in Dashboard', async () => {
                render(
                        <MemoryRouter>
                                <Dashboard />
                        </MemoryRouter>
                )

                await screen.findByText('First Project')
                expect(screen.getByText(/approved/i)).toBeInTheDocument()

                await screen.findByText('Second Project')
                expect(screen.getByText(/pending approval/i)).toBeInTheDocument()
        })
})

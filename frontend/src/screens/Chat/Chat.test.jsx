import { render, screen, waitFor, vi } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'
import { BrowserRouter } from 'react-router-dom'
import Chat from './Chat'

describe('Proposal Drafter – Form validation', () => {
        it('disables the Generate button until all required inputs are filled', async () => {
                server.use(
                        http.get('http://localhost:8502/api/templates', () => {
                                return HttpResponse.json({ templates: { "UNHCR": {}, "IOM": {} } })
                        }),
                        http.get('http://localhost:8502/api/profile', () => {
                                return HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })
                        })
                )
                render(
                        <BrowserRouter>
                                <Chat />
                        </BrowserRouter>
                )

                const generateButton = screen.getByRole('button', { name: /generate/i })
                expect(generateButton).toBeDisabled()

                const textarea = screen.getByPlaceholderText(/Provide as much details as possible on your initial project idea!/i)
                await userEvent.type(textarea, 'School for the disabled in New York')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const projectTitleInput = screen.getByLabelText(/Project Draft Short name/i)
                await userEvent.type(projectTitleInput, 'Accessible School')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const geographicalScopeInput = screen.getByLabelText(/Geographical Scope/i)
                await userEvent.type(geographicalScopeInput, 'NYC')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const countryInput = screen.getByLabelText(/Country \/ Location\(s\)/i)
                await userEvent.type(countryInput, 'USA')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const beneficiariesProfileInput = screen.getByLabelText(/Beneficiaries Profile/i)
                await userEvent.type(beneficiariesProfileInput, 'Students')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const durationInput = screen.getByLabelText(/Duration/i)
                await userEvent.type(durationInput, '12 months')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const budgetInput = screen.getByLabelText(/Budget Range/i)
                await userEvent.type(budgetInput, '1M$')
                await waitFor(() => expect(generateButton).toBeDisabled())

                const mainOutcomeButton = screen.getByRole('button', { name: /Select Main Outcome/i })
                await userEvent.click(mainOutcomeButton)
                await userEvent.click(screen.getByLabelText('OA1-Access/Documentation'))
                await userEvent.click(screen.getByText('Close'))
                await waitFor(() => expect(generateButton).toBeDisabled())

                const donorInput = screen.getByLabelText(/Targeted Donor/i)
                await userEvent.type(donorInput, 'USAID')
                await waitFor(() => expect(generateButton).toBeEnabled())
        })
})

describe('Proposal Drafter – One‑Section Generation Flow', () => {
        it('calls process_section with session and body, renders all cards', async () => {
                server.use(
                        http.get('http://localhost:8502/api/templates', () => HttpResponse.json({ templates: { "UNHCR": {}, "IOM": {} } })),
                        http.get('http://localhost:8502/api/profile', () => HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })),
                        http.post('http://localhost:8502/api/create-session', () => {
                                return HttpResponse.json({
                                        session_id: 'test-session-id',
                                        proposal_id: 'test-proposal-id',
                                        proposal_template: {
                                                sections: [
                                                        { section_name: 'Summary' }, { section_name: 'Rationale' }, { section_name: 'Project Description' },
                                                        { section_name: 'Partnerships and Coordination' }, { section_name: 'Monitoring' }, { section_name: 'Evaluation' },
                                                ]
                                        }
                                })
                        }),
                        http.post('http://localhost:8502/api/process_section/:session_id', async ({request}) => {
                                const body = await request.json()
                                return HttpResponse.json({ generated_text: `Mocked text for ${body.section}` })
                        })
                )
                render(
                        <BrowserRouter>
                                <Chat />
                        </BrowserRouter>
                )

                await userEvent.type(screen.getByPlaceholderText(/Provide as much details as possible on your initial project idea!/i), 'School for the disabled in New York')
                await userEvent.type(screen.getByLabelText(/Project Draft Short name/i), 'Accessible School')
                const mainOutcomeButton = screen.getByRole('button', { name: /Select Main Outcome/i })
                await userEvent.click(mainOutcomeButton)
                await userEvent.click(screen.getByLabelText('OA1-Access/Documentation'))
                await userEvent.click(screen.getByText('Close'))
                await userEvent.type(screen.getByLabelText(/Geographical Scope/i), 'NYC')
                await userEvent.type(screen.getByLabelText(/Country \/ Location\(s\)/i), 'USA')
                await userEvent.type(screen.getByLabelText(/Beneficiaries Profile/i), 'Students')
                await userEvent.type(screen.getByLabelText(/Duration/i), '12 months')
                await userEvent.type(screen.getByLabelText(/Budget Range/i), '1M$')
                await userEvent.type(screen.getByLabelText(/Targeted Donor/i), 'USAID')

                await userEvent.click(screen.getByRole('button', { name: /generate/i }))

                const sections = ['Summary','Rationale','Project Description', "Partnerships and Coordination", "Monitoring", "Evaluation"]

                for (const sec of sections) {
                        const card = await screen.findByText(new RegExp(`Mocked text for ${sec}`, 'i'), { timeout: 10000 });
                        expect(card).toBeInTheDocument();
                }
        })

        it('allows editing Summary content', async () => {
                server.use(
                        http.get('http://localhost:8502/api/templates', () => HttpResponse.json({ templates: { "UNHCR": {}, "IOM": {} } })),
                        http.get('http://localhost:8502/api/profile', () => HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })),
                        http.post('http://localhost:8502/api/create-session', () => {
                                return HttpResponse.json({
                                        session_id: 'test-session-id',
                                        proposal_id: 'test-proposal-id',
                                        proposal_template: {
                                                sections: [
                                                        { section_name: 'Summary' }, { section_name: 'Rationale' }, { section_name: 'Project Description' },
                                                        { section_name: 'Partnerships and Coordination' }, { section_name: 'Monitoring' }, { section_name: 'Evaluation' },
                                                ]
                                        }
                                })
                        }),
                        http.post('http://localhost:8502/api/process_section/:session_id', async ({request}) => {
                                const body = await request.json()
                                return HttpResponse.json({ generated_text: `Mocked text for ${body.section}` })
                        }),
                        http.post('http://localhost:8502/api/update-section-content', async ({request}) => {
                                const body = await request.json()
                                return HttpResponse.json({ content: body.content })
                        })
                )
                render(
                        <BrowserRouter>
                                <Chat />
                        </BrowserRouter>
                )

                await userEvent.type(screen.getByPlaceholderText(/Provide as much details as possible on your initial project idea!/i), 'School for the disabled in New York')
                await userEvent.type(screen.getByLabelText(/Project Draft Short name/i), 'Accessible School')
                const mainOutcomeButton = screen.getByRole('button', { name: /Select Main Outcome/i })
                await userEvent.click(mainOutcomeButton)
                await userEvent.click(screen.getByLabelText('OA1-Access/Documentation'))
                await userEvent.click(screen.getByText('Close'))
                await userEvent.type(screen.getByLabelText(/Geographical Scope/i), 'NYC')
                await userEvent.type(screen.getByLabelText(/Country \/ Location\(s\)/i), 'USA')
                await userEvent.type(screen.getByLabelText(/Beneficiaries Profile/i), 'Students')
                await userEvent.type(screen.getByLabelText(/Duration/i), '12 months')
                await userEvent.type(screen.getByLabelText(/Budget Range/i), '1M$')
                await userEvent.type(screen.getByLabelText(/Targeted Donor/i), 'USAID')

                await userEvent.click(screen.getByRole('button', { name: /generate/i }))

                const sections = ['Summary','Rationale','Project Description', "Partnerships and Coordination", "Monitoring", "Evaluation"]

                for (const sec of sections) {
                        const card = await screen.findByText(new RegExp(`Mocked text for ${sec}`, 'i'), { timeout: 10000 });
                        expect(card).toBeInTheDocument();
                }

                const editButton = screen.getByLabelText('edit-section-0')
                expect(editButton).toBeInTheDocument()

                await userEvent.click(editButton)

                const editor = screen.getByRole('textbox', { name: /editor for Summary/i })
                expect(editor).toBeInTheDocument()
                expect(editor).toHaveValue('Mocked text for Summary')

                await userEvent.clear(editor)
                await userEvent.type(editor, 'Custom Summary Text')

                await userEvent.click(editButton)

                const regenerated = await screen.findByText(/Custom Summary Text/i)
                expect(regenerated).toBeInTheDocument()
        }),

        it('hides the input form when a finalized proposal is loaded', async () => {
                server.use(
                        http.get('http://localhost:8502/api/templates', () => HttpResponse.json({ templates: { "UNHCR": {}, "IOM": {} } })),
                        http.get('http://localhost:8502/api/profile', () => HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })),
                        http.get('http://localhost:8502/api/load-draft/:proposal_id', () => {
                                return HttpResponse.json({
                                        proposal_id: 'approved-proposal-123',
                                        session_id: 'test-session-id',
                                        project_description: 'test description',
                                        form_data: {
                                                "Project Draft Short name": "test project", "Main Outcome": ["OA1-Access/Documentation"],
                                                "Beneficiaries Profile": "test beneficiaries", "Potential Implementing Partner": "test partner",
                                                "Geographical Scope": "test scope", "Country / Location(s)": "test country",
                                                "Budget Range": "1M$", "Duration": "12 months", "Targeted Donor": "USAID"
                                        },
                                        generated_sections: { 'Summary': 'Mocked text for Summary' },
                                        is_accepted: true
                                })
                        })
                )

                sessionStorage.setItem('proposal_id', 'approved-proposal-123')
                render(
                        <BrowserRouter>
                                <Chat />
                        </BrowserRouter>
                )

                await screen.findByText('Results')

                expect(screen.queryByPlaceholderText(/Provide as much details as possible on your initial project idea!/i)).not.toBeInTheDocument()
        })
})

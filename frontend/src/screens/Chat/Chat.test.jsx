/// <reference types="vitest" />
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'
import { BrowserRouter } from 'react-router-dom'
import { WizardProvider } from '../../context/WizardContext'
import Chat from './Chat'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

vi.mock('../../context/AuthContext', () => ({
        useAuth: () => ({
                user: { id: 'user-1', name: 'Test User', email: 'test@test.com', is_admin: false },
                loading: false,
                roles: ['proposal writer'],
                memberships: [],
                activeTeam: null,
                switchTeam: vi.fn(),
        }),
}))

async function selectOption(label, optionName) {
        const input = screen.getByLabelText(label)
        await userEvent.click(input)
        await userEvent.type(input, optionName)
        await userEvent.click(await screen.findByRole('option', { name: optionName }))
}

async function selectFirstOption(label) {
        const input = screen.getByLabelText(label)
        await userEvent.click(input)
        await userEvent.keyboard('{ArrowDown}{Enter}')
}

vi.mock('../../utils/downloadFile', () => ({
        default: vi.fn(),
}))

beforeEach(() => {
        server.use(
                http.get(`${API_BASE_URL}/users/me/approved-settings`, () =>
                        HttpResponse.json({
                                approved_settings: [{
                                        setting_type: 'field_context_focal',
                                        setting_value: '1',
                                        status: 'approved'
                                }]
                        })
                )
        )
})

describe('Proposal Drafter – Form validation', () => {
        it('disables the Generate button until all required inputs are filled', async () => {
                server.use(
                        http.get(`${API_BASE_URL}/templates`, () => {
                                return HttpResponse.json({ templates: { "UNHCR": {} } })
                        }),
                        http.get(`${API_BASE_URL}/profile`, () => {
                                return HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })
                        }),
                        http.get(`${API_BASE_URL}/donors`, () => {
                                return HttpResponse.json({ donors: [{id: '1', name: 'USAID'}] });
                        }),
                        http.get(`${API_BASE_URL}/outcomes`, () => {
                                return HttpResponse.json({ outcomes: [{id: '1', name: 'OA1-Access/Documentation'}] });
                        }),
                        http.get(`${API_BASE_URL}/field-contexts`, () => {
                                return HttpResponse.json({ field_contexts: [{id: '1', name: 'USA', geographic_coverage: 'One Country Operation'}] });
                        }),
                        http.get(`${API_BASE_URL}/users`, () => {
                                return HttpResponse.json({ users: [] });
                        })
                )
                render(
                        <BrowserRouter>
                                <WizardProvider>
                                        <Chat />
                                </WizardProvider>
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

                const geographicalScopeInput = screen.getByTestId('geographical-scope')
                await userEvent.selectOptions(geographicalScopeInput, 'One Country Operation')
                await waitFor(() => expect(generateButton).toBeDisabled())

                await selectFirstOption(/Country \/ Location\(s\)/i)
                await waitFor(() => expect(generateButton).toBeDisabled())

                const beneficiariesProfileInput = screen.getByLabelText(/Beneficiaries Profile/i)
                await userEvent.type(beneficiariesProfileInput, 'Students')
                await waitFor(() => expect(generateButton).toBeDisabled())

                await selectOption(/Duration/i, '12 months')
                await waitFor(() => expect(generateButton).toBeDisabled())

                await selectOption(/Budget Range/i, '1M$')
                await waitFor(() => expect(generateButton).toBeDisabled())

                await selectOption('Main Outcome', 'OA1-Access/Documentation')
                await waitFor(() => expect(generateButton).toBeDisabled())

                await selectOption(/Targeted Donor/i, 'USAID')
                await waitFor(() => expect(generateButton).toBeEnabled())
        }, 20000)
})

describe('Proposal Drafter – One‑Section Generation Flow', () => {
        it('calls process_section with session and body, renders all cards', async () => {
                server.use(
                        http.get(`${API_BASE_URL}/templates`, () => HttpResponse.json({ templates: { "UNHCR": {} } })),
                        http.get(`${API_BASE_URL}/profile`, () => HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })),
                        http.get(`${API_BASE_URL}/donors`, () => {
                                return HttpResponse.json({ donors: [{id: '1', name: 'USAID'}] });
                        }),
                        http.get(`${API_BASE_URL}/outcomes`, () => {
                                return HttpResponse.json({ outcomes: [{id: '1', name: 'OA1-Access/Documentation'}] });
                        }),
                        http.get(`${API_BASE_URL}/field-contexts`, () => {
                                return HttpResponse.json({ field_contexts: [{id: '1', name: 'USA', geographic_coverage: 'One Country Operation'}] });
                        }),
                        http.get(`${API_BASE_URL}/users`, () => {
                                return HttpResponse.json({ users: [] });
                        }),
                        http.post(`${API_BASE_URL}/create-session`, () => {
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
                        http.post(`${API_BASE_URL}/generate-proposal-sections/:session_id`, async () => {
                                return new HttpResponse(null, { status: 200 });
                        }),
                        http.get(`${API_BASE_URL}/proposals/:proposal_id/status`, async () => {
                                return HttpResponse.json({
                                        status: 'done',
                                        generated_sections: {
                                                'Summary': 'Mocked text for Summary',
                                                'Rationale': 'Mocked text for Rationale',
                                                'Project Description': 'Mocked text for Project Description',
                                                'Partnerships and Coordination': 'Mocked text for Partnerships and Coordination',
                                                'Monitoring': 'Mocked text for Monitoring',
                                                'Evaluation': 'Mocked text for Evaluation',
                                        },
                                        proposal_template: {
                                                sections: [
                                                        { section_name: 'Summary' }, { section_name: 'Rationale' }, { section_name: 'Project Description' },
                                                        { section_name: 'Partnerships and Coordination' }, { section_name: 'Monitoring' }, { section_name: 'Evaluation' },
                                                ]
                                        }
                                })
                        })
                )
                render(
                        <BrowserRouter>
                                <WizardProvider>
                                        <Chat />
                                </WizardProvider>
                        </BrowserRouter>
                )

                await userEvent.type(screen.getByPlaceholderText(/Provide as much details as possible on your initial project idea!/i), 'School for the disabled in New York')
                await userEvent.type(screen.getByLabelText(/Project Draft Short name/i), 'Accessible School')
                const mainOutcomeButton = screen.getByLabelText('Main Outcome')
                await userEvent.type(mainOutcomeButton, 'OA1-Access/Documentation{enter}')
                const geographicalScopeInput = screen.getByTestId('geographical-scope')
                await userEvent.selectOptions(geographicalScopeInput, 'One Country Operation')
                await userEvent.type(screen.getByLabelText(/Country \/ Location\(s\)/i), 'USA{enter}')
                await userEvent.type(screen.getByLabelText(/Beneficiaries Profile/i), 'Students')
                await userEvent.type(screen.getByLabelText(/Duration/i), '12 months{enter}')
                await userEvent.type(screen.getByLabelText(/Budget Range/i), '1M${enter}')
                await userEvent.type(screen.getByLabelText(/Targeted Donor/i), 'USAID{enter}')

                await userEvent.click(screen.getByRole('button', { name: /generate/i }))

                await waitFor(async () => {
                        await screen.findByText('Results')
                }, { timeout: 10000 })

                const sections = ['Summary','Rationale','Project Description', "Partnerships and Coordination", "Monitoring", "Evaluation"]

                for (const sec of sections) {
                        const kebabSectionName = sec.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
                        await waitFor(async () => {
                                const sectionContent = await screen.findByTestId(`section-content-${kebabSectionName}`);
                                expect(sectionContent).toHaveTextContent(new RegExp(`Mocked text for ${sec}`, 'i'));
                        }, { timeout: 10000 });
                }
        }, 20000)

        it('allows editing Summary content', async () => {
                server.use(
                        http.get(`${API_BASE_URL}/templates`, () => HttpResponse.json({ templates: { "UNHCR": {} } })),
                        http.get(`${API_BASE_URL}/profile`, () => HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })),
                        http.get(`${API_BASE_URL}/donors`, () => {
                                return HttpResponse.json({ donors: [{id: '1', name: 'USAID'}] });
                        }),
                        http.get(`${API_BASE_URL}/outcomes`, () => {
                                return HttpResponse.json({ outcomes: [{id: '1', name: 'OA1-Access/Documentation'}] });
                        }),
                        http.get(`${API_BASE_URL}/field-contexts`, () => {
                                return HttpResponse.json({ field_contexts: [{id: '1', name: 'USA', geographic_coverage: 'One Country Operation'}] });
                        }),
                        http.get(`${API_BASE_URL}/users`, () => {
                                return HttpResponse.json({ users: [] });
                        }),
                        http.post(`${API_BASE_URL}/create-session`, () => {
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
                        http.post(`${API_BASE_URL}/generate-proposal-sections/:session_id`, async () => {
                                return new HttpResponse(null, { status: 200 });
                        }),
                        http.get(`${API_BASE_URL}/proposals/:proposal_id/status`, async () => {
                                return HttpResponse.json({
                                        status: 'done',
                                        generated_sections: {
                                                'Summary': 'Mocked text for Summary',
                                                'Rationale': 'Mocked text for Rationale',
                                                'Project Description': 'Mocked text for Project Description',
                                                'Partnerships and Coordination': 'Mocked text for Partnerships and Coordination',
                                                'Monitoring': 'Mocked text for Monitoring',
                                                'Evaluation': 'Mocked text for Evaluation',
                                        },
                                        proposal_template: {
                                                sections: [
                                                        { section_name: 'Summary' }, { section_name: 'Rationale' }, { section_name: 'Project Description' },
                                                        { section_name: 'Partnerships and Coordination' }, { section_name: 'Monitoring' }, { section_name: 'Evaluation' },
                                                ]
                                        }
                                })
                        }),
                        http.post(`${API_BASE_URL}/update-section-content`, async ({request}) => {
                                const body = await request.json()
                                return HttpResponse.json({ content: body.content })
                        })
                )
                render(
                        <BrowserRouter>
                                <WizardProvider>
                                        <Chat />
                                </WizardProvider>
                        </BrowserRouter>
                )

                await userEvent.type(screen.getByPlaceholderText(/Provide as much details as possible on your initial project idea!/i), 'School for the disabled in New York')
                await userEvent.type(screen.getByLabelText(/Project Draft Short name/i), 'Accessible School')
                const mainOutcomeButton = screen.getByLabelText('Main Outcome')
                await userEvent.type(mainOutcomeButton, 'OA1-Access/Documentation{enter}')
                const geographicalScopeInput = screen.getByTestId('geographical-scope')
                await userEvent.selectOptions(geographicalScopeInput, 'One Country Operation')
                await userEvent.type(screen.getByLabelText(/Country \/ Location\(s\)/i), 'USA{enter}')
                await userEvent.type(screen.getByLabelText(/Beneficiaries Profile/i), 'Students')
                await userEvent.type(screen.getByLabelText(/Duration/i), '12 months{enter}')
                await userEvent.type(screen.getByLabelText(/Budget Range/i), '1M${enter}')
                await userEvent.type(screen.getByLabelText(/Targeted Donor/i), 'USAID{enter}')

                await userEvent.click(screen.getByRole('button', { name: /generate/i }))

                await waitFor(async () => {
                        await screen.findByText('Results')
                }, { timeout: 10000 })

                const sections = ['Summary','Rationale','Project Description', "Partnerships and Coordination", "Monitoring", "Evaluation"]

                for (const sec of sections) {
                        const kebabSectionName = sec.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
                        await waitFor(async () => {
                                const sectionContent = await screen.findByTestId(`section-content-${kebabSectionName}`);
                                expect(sectionContent).toHaveTextContent(new RegExp(`Mocked text for ${sec}`, 'i'));
                        }, { timeout: 10000 });
                }

                const editButton = screen.getByTestId('edit-save-button-summary')
                expect(editButton).toBeInTheDocument()

                await userEvent.click(editButton)

                const editor = screen.getByTestId('section-editor-summary')
                expect(editor).toBeInTheDocument()
                expect(editor).toHaveValue('Mocked text for Summary')

                await userEvent.clear(editor)
                await userEvent.type(editor, 'Custom Summary Text')

                await userEvent.click(editButton)

                const regenerated = await screen.findByText(/Custom Summary Text/i)
                expect(regenerated).toBeInTheDocument()
        }, 20000),

        it('hides the input form when a submitted proposal is loaded', async () => {
                server.use(
                        http.get(`${API_BASE_URL}/templates`, () => HttpResponse.json({ templates: { "UNHCR": {} } })),
                        http.get(`${API_BASE_URL}/profile`, () => HttpResponse.json({ user: { "email": "test@test.com", "name": "Test User" } })),
                        http.get(`${API_BASE_URL}/donors`, () => {
                                return HttpResponse.json({ donors: [{id: '1', name: 'USAID'}] });
                        }),
                        http.get(`${API_BASE_URL}/outcomes`, () => {
                                return HttpResponse.json({ outcomes: [{id: '1', name: 'OA1-Access/Documentation'}] });
                        }),
                        http.get(`${API_BASE_URL}/field-contexts`, () => {
                                return HttpResponse.json({ field_contexts: [{id: '1', name: 'USA', geographic_coverage: 'One Country Operation'}] });
                        }),
                        http.get(`${API_BASE_URL}/users`, () => {
                                return HttpResponse.json({ users: [] });
                        }),
                        http.get(`${API_BASE_URL}/load-draft/:proposal_id`, () => {
                                return HttpResponse.json({
                                        proposal_id: 'submitted-proposal-123',
                                        session_id: 'test-session-id',
                                        project_description: 'test description',
                                        form_data: {
                                                "Project Draft Short name": "test project", "Main Outcome": ["1"],
                                                "Beneficiaries Profile": "test beneficiaries", "Potential Implementing Partner": "test partner",
                                                "Geographical Scope": "One Country Operation", "Country / Location(s)": "1",
                                                "Budget Range": "1M$", "Duration": "12 months", "Targeted Donor": "1"
                                        },
                                        generated_sections: { 'Summary': 'Mocked text for Summary' },
                                        status: 'submitted',
                                        proposal_template: {
                                                sections: [{ section_name: 'Summary' }]
                                        }
                                })
                        }),
                        http.get(`${API_BASE_URL}/proposals/:proposal_id/status-history`, () => {
                                return HttpResponse.json({ statuses: [] });
                        })
                )

                sessionStorage.setItem('proposal_id', 'submitted-proposal-123')
                render(
                        <BrowserRouter>
                                <WizardProvider>
                                        <Chat />
                                </WizardProvider>
                        </BrowserRouter>
                )

                await waitFor(async () => {
                        await screen.findByText('Results')
                })

                expect(screen.queryByPlaceholderText(/Provide as much details as possible on your initial project idea!/i)).not.toBeInTheDocument()
        })
})

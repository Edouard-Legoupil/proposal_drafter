import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

export const server = setupServer(
        http.get(`${API_BASE_URL}/profile`, () =>
                HttpResponse.json({
                        user: {
                                name: "Edouard",
                                email: "edouard.legoupil@gmail.com"
                        }
                })
        ),

        http.post(`${API_BASE_URL}/login`, async ({ request }) => {
                const { email, password } = await request.json()

                if (email === 'edouard.legoupil@gmail.com' && password === 'edouard123')
                {
                        return new HttpResponse(null, {
                                status: 200,
                                headers: { 'Set-Cookie': 'token=fake-token HttpOnly Path=/ Secure' }
                        })
                }
                else
                {
                        return new HttpResponse(
                                JSON.stringify({ message: 'Invalid credentials' }),
                                { status: 401, headers: { 'Content-Type': 'application/json' } }
                        )
                }
        }),

        http.post(`${API_BASE_URL}/get-security-question`, async ({ request }) => {
                const { email } = await request.json()
                if (email === 'user@example.com') {
                        return HttpResponse.json({ question: "What's your pet's name?" })
                }
                return new HttpResponse(JSON.stringify({ error: 'Email not found' }), {
                        status: 404, headers: { 'Content-Type': 'application/json'
                }})
        }),

        http.post(`${API_BASE_URL}/verify-security-answer`, async ({ request }) => {
                const { email, security_answer } = await request.json()
                if (email === 'user@example.com' && security_answer === 'fluffy') {
                        return new HttpResponse(null, { status: 200 })
                }
                return new HttpResponse(JSON.stringify({ error: 'Incorrect answer' }), {
                        status: 401, headers: { 'Content-Type': 'application/json'
                }})
        }),

        http.post(`${API_BASE_URL}/update-password`, async ({ request }) => {
                const { email, security_answer, new_password } = await request.json()
                if (email === 'user@example.com' && security_answer === 'fluffy' && new_password.length >= 8) {
                        return new HttpResponse(null, {
                                status: 200,
                                headers: { 'Set-Cookie': 'token=reset-token; HttpOnly; Path=/; Secure' }
                        })
                }
                return new HttpResponse(JSON.stringify({ error: 'Reset failed' }), {
                        status: 400, headers: { 'Content-Type': 'application/json'
                }})
        }),

        http.get(`${API_BASE_URL}/list-drafts`, () =>
                HttpResponse.json({
                        drafts: [
                                {
                                        proposal_id: '1',
                                        project_title: 'First Project',
                                        summary: 'Sum1',
                                        updated_at: '2025-05-10T10:00:00.123Z',
                                        is_accepted: true
                                },
                                {
                                        proposal_id: '2',
                                        project_title: 'Second Project',
                                        summary: 'Sum2',
                                        updated_at: '2025-05-11T11:30:00.456Z',
                                        is_accepted: false
                                }
                        ]
                })
        ),

        http.get(`${API_BASE_URL}/users`, () => {
                return HttpResponse.json({
                        users: [
                                { id: '1', name: 'User 1' },
                                { id: '2', name: 'User 2' },
                        ]
                })
        }),

        http.get(`${API_BASE_URL}/outcomes`, () => {
                return HttpResponse.json({
                        outcomes: [
                                { id: '1', name: 'OA1-Access/Documentation' },
                                { id: '2', name: 'OA2-Something Else' },
                        ]
                })
        }),

        http.post(`${API_BASE_URL}/donors`, async ({ request }) => {
                const { name } = await request.json()
                return HttpResponse.json({ id: `new_${name}`, name: name })
        }),

        http.post(`${API_BASE_URL}/field-contexts`, async ({ request }) => {
                const { name } = await request.json()
                return HttpResponse.json({ id: `new_${name}`, name: name })
        }),

        http.post(`${API_BASE_URL}/outcomes`, async ({ request }) => {
                const { name } = await request.json()
                return HttpResponse.json({ id: `new_${name}`, name: name })
        }),

        http.get(`${API_BASE_URL}/proposals/reviews`, () => {
                return HttpResponse.json({
                        reviews: [
                                {
                                        proposal_id: '3',
                                        project_title: 'Third Project',
                                        summary: 'Sum3',
                                        updated_at: '2025-05-12T12:00:00.123Z',
                                        is_accepted: false
                                }
                        ]
                })
        }),

        http.get(new RegExp(`${API_BASE_URL}/load-draft/.*`), async ({ request }) => {
                const url = new URL(request.url)
                const segments = url.pathname.split('/')
                const proposalId = segments[segments.length - 1]

                const isAccepted = proposalId === 'approved-proposal-123'

                const generated_sections = Object.fromEntries(
                        proposalTemplate.sections.map(s => [s.section_name, ""])
                      )

                return HttpResponse.json({
                        proposal_id: 'fake-proposal-id',
                        session_id: 'fake-session-id',
                        project_description: '',
                        form_data: Object.fromEntries(
                                Object.entries({
                                'Project title': '',
                                'Project type': '',
                                'Secondary project type': '',
                                'Geographical Coverage': '',
                                'Executing agency': '',
                                'Beneficiaries': '',
                                'Partner(s)': '',
                                'Management site': '',
                                'Duration': '',
                                'Budget': ''
                                }).map(([k]) => [k, ''])
                        ),
                        generated_sections,
                        // generated_sections: {
                        //         Summary: '',
                        //         Rationale: '',
                        //         'Project Description': '',
                        //         'Partnerships and Coordination': '',
                        //         Monitoring: '',
                        //         Evaluation: '',
                        //         'Results Matrix': '',
                        //         'Work Plan': '',
                        //         'Budget': '',
                        //         'Annex 1. Risk Assessment Plan': ''
                        // },
                        is_accepted: isAccepted
                })
        }),

        http.post(new RegExp(`${API_BASE_URL}/regenerate_section/.*`), async ({ request }) => {
                const { section } = await request.json()
                return HttpResponse.json({ generated_text: `Custom ${section} text` })
        }),

        http.post(`${API_BASE_URL}/store_base_data`, async () => {
                return HttpResponse.json({ session_id: 'fake-session-id' })
        }),

        http.post(`${API_BASE_URL}/save-draft`, async () => {
                return HttpResponse.json({ proposal_id: 'fake-proposal-id' })
        }),

        http.post(new RegExp(`${API_BASE_URL}/process_section/.*`), async ({ request }) => {
                const { section } = await request.json()
                return new Promise(res => {
                        setTimeout(() => {
                                res(
                                        HttpResponse.json({ generated_text: `Mocked text for ${section}` })
                                )
                        }, 50)
                })
        }),

        http.post(`${API_BASE_URL}/finalize-proposal`, () =>
                HttpResponse.json({ success: true })
        ),

        http.get(`${API_BASE_URL}/metrics/development-time`, () => {
                return HttpResponse.json({ "Proposal": 30, "Revision": 15 });
        }),

        http.get(`${API_BASE_URL}/metrics/funding-by-category`, () => {
                return HttpResponse.json({ "Health": 5, "Education": 10 });
        }),

        http.get(`${API_BASE_URL}/metrics/donor-interest`, () => {
                return HttpResponse.json({ "USAID": 20, "UNICEF": 5 });
        }),

        http.get(`${API_BASE_URL}/knowledge-cards`, () => {
                return HttpResponse.json({ knowledge_cards: [] });
        })
)

import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"
const apiPath = API_BASE_URL.replace(/https?:\/\/[^/]+/, '')
const normalizedApiBase = apiPath.replace(/\/$/, '')
const buildApiRegex = (path) => new RegExp(`.*${normalizedApiBase}${path}`)

// Minimal mock template for load-draft endpoint
const proposalTemplate = { sections: [] };

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
                const payload = await request.json()
                const identifier = payload.identifier || payload.email
                const password = payload.password

                if (!identifier || !password) {
                        return new HttpResponse(
                                JSON.stringify({ error: 'Missing credentials' }),
                                { status: 400, headers: { 'Content-Type': 'application/json' } }
                        )
                }

                if (identifier === 'edouard.legoupil@gmail.com' && password === 'edouard123') {
                        return new HttpResponse(HttpResponse.json({}), {
                                status: 200,
                                headers: { 'Set-Cookie': 'token=fake-token HttpOnly Path=/ Secure' }
                        })
                }

                return new HttpResponse(HttpResponse.json({}), {
                        status: 200,
                        headers: { 'Set-Cookie': 'token=fake-token HttpOnly Path=/ Secure' }
                })
        }),

        http.post(`${API_BASE_URL}/get-security-question`, async ({ request }) => {
                const { email } = await request.json()
                if (email === 'user@example.com') {
                        return HttpResponse.json({ question: "What's your pet's name?" })
                }
                return new HttpResponse(JSON.stringify({ error: 'Email not found' }), {
                        status: 404, headers: {
                                'Content-Type': 'application/json'
                        }
                })
        }),

        http.post(`${API_BASE_URL}/verify-security-answer`, async ({ request }) => {
                const { email, security_answer } = await request.json()
                if (email === 'user@example.com' && security_answer === 'fluffy') {
                        return new HttpResponse(null, { status: 200 })
                }
                return new HttpResponse(JSON.stringify({ error: 'Incorrect answer' }), {
                        status: 401, headers: {
                                'Content-Type': 'application/json'
                        }
                })
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
                        status: 400, headers: {
                                'Content-Type': 'application/json'
                        }
                })
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

        http.get(`${API_BASE_URL}/list-all-proposals`, () =>
                HttpResponse.json({ proposals: [] })
        ),

        http.get(`${API_BASE_URL}/teams`, () =>
                HttpResponse.json({ teams: [] })
        ),

        http.get(buildApiRegex('/templates'), () =>
                HttpResponse.json({ templates: { "UNHCR": { sections: [] } } })
        ),

        http.get(buildApiRegex('/donors'), () =>
                HttpResponse.json({ donors: [{ id: '1', name: 'USAID' }] })
        ),

        http.get(buildApiRegex('/field-contexts'), () =>
                HttpResponse.json({ field_contexts: [{ id: '1', name: 'USA', geographic_coverage: 'One Country Operation' }] })
        ),

        http.get(buildApiRegex('/geographic-coverages'), () =>
                HttpResponse.json({ geographic_coverages: ['One Country Operation'] })
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
                const isSubmitted = proposalId === 'submitted-proposal-123'
                const status = isSubmitted ? 'submitted' : 'draft'
                const sectionNames = [
                        'Summary',
                        'Rationale',
                        'Project Description',
                        'Partnerships and Coordination',
                        'Monitoring',
                        'Evaluation'
                ]

                const generated_sections = Object.fromEntries(
                        sectionNames.map(name => [name, isSubmitted ? `Mocked text for ${name}` : ""])
                )

                const formDataDefaults = isSubmitted
                        ? {
                                "Project Draft Short name": "test project",
                                "Main Outcome": ["1"],
                                "Beneficiaries Profile": "test beneficiaries",
                                "Potential Implementing Partner": "test partner",
                                "Geographical Scope": "One Country Operation",
                                "Country / Location(s)": "1",
                                "Budget Range": "1M$",
                                "Duration": "12 months",
                                "Targeted Donor": "1"
                        }
                        : {
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
                        }

                return HttpResponse.json({
                        proposal_id: 'fake-proposal-id',
                        session_id: 'fake-session-id',
                        project_description: isSubmitted ? 'test description' : '',
                        form_data: formDataDefaults,
                        generated_sections,
                        status,
                        proposal_template: {
                                sections: sectionNames.map(name => ({ section_name: name }))
                        },
                        is_accepted: isAccepted
                })
        }),

        http.post(`${API_BASE_URL}/regenerate_section/:proposal_id`, async ({ request }) => {
                const { section } = await request.json()
                return HttpResponse.json({ generated_text: `Custom ${section} text` })
        }),

        http.get(`${API_BASE_URL}/sso-status`, () => {
                return HttpResponse.json({ sso_enabled: false })
        }),

		http.post(buildApiRegex('/create-session'), async () =>
			HttpResponse.json({
				session_id: 'fake-session-id',
				proposal_id: 'fake-proposal-id',
				proposal_template: {
					sections: [
						{ section_name: 'Summary' },
						{ section_name: 'Rationale' },
						{ section_name: 'Project Description' },
						{ section_name: 'Partnerships and Coordination' },
						{ section_name: 'Monitoring' },
						{ section_name: 'Evaluation' }
					]
				}
			})
		),

		http.post(buildApiRegex('/generate-proposal-sections/.*'), () =>
			HttpResponse.json({ success: true })
		),

		http.get(buildApiRegex('/proposals/.*/status'), () =>
			HttpResponse.json({
				status: 'done',
				generated_sections: {
					Summary: 'Mocked text for Summary',
					Rationale: 'Mocked text for Rationale',
					'Project Description': 'Mocked text for Project Description',
					'Partnerships and Coordination': 'Mocked text for Partnerships and Coordination',
					Monitoring: 'Mocked text for Monitoring',
					Evaluation: 'Mocked text for Evaluation'
				},
				proposal_template: {
					sections: [
						{ section_name: 'Summary' },
						{ section_name: 'Rationale' },
						{ section_name: 'Project Description' },
						{ section_name: 'Partnerships and Coordination' },
						{ section_name: 'Monitoring' },
						{ section_name: 'Evaluation' }
					]
				}
			})
		),

		http.get(buildApiRegex('/generate-tables/.*'), () =>
			new HttpResponse("dummy-table-content", {
				status: 200,
				headers: {
					'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
					'Content-Disposition': 'attachment; filename="proposal-tables.xlsx"'
				}
			})
		),

		http.post(buildApiRegex('/update_section/.*'), async ({ request }) => {
			const { section } = await request.json()
			return HttpResponse.json({ generated_text: `Custom ${section} text` })
		}),

		http.get(buildApiRegex('/proposals/.*/peer-reviews'), () =>
			HttpResponse.json({ reviews: [] })
		),

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

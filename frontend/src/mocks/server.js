import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

export const server = setupServer(
        http.post(`${API_BASE_URL}/store_base_data`, async ({ request }) => {
                const { project_description, form_data } = await request.json()

                return new HttpResponse(
                        JSON.stringify({ session_id: 'test-session-123' }),
                        { status: 200, headers: { 'Content-Type': 'application/json' } }
                )
        }),

        http.post(`${API_BASE_URL}/process_section/:sessionId`, async ({ request, params }) => {
                const sessionId = params.sessionId
                const { section } = await request.json()

                await new Promise((r) => setTimeout(r, 100))

                return new HttpResponse(
                        JSON.stringify({
                                generated_text: `Mocked text for ${section}`,
                        }),
                        {
                                status: 200,
                                headers: { 'Content-Type': 'application/json' },
                        }
                )
        }),

        http.post(`${API_BASE_URL}/regenerate_section/:sessionId`, async ({ request, params }) => {
                const sessionId = params.sessionId
                const { section, concise_input } = await request.json()

                await new Promise((r) => setTimeout(r, 100))

                return new HttpResponse(
                        JSON.stringify({
                                generated_text: `Regen for ${section}: ${concise_input}`,
                        }),
                        {
                                status: 200,
                                headers: { 'Content-Type': 'application/json' },
                        }
                )
        })
)

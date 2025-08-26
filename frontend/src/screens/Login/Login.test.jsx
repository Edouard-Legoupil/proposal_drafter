import { vi, describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'
import Login from './Login'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom')
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    }
})

describe('Login Form Validation', () => {
        it('disables the login button for invalid or empty inputs', async () => {
                render(
                        <BrowserRouter>
                                <Login />
                        </BrowserRouter>
                )

                const emailInput = screen.getByLabelText(/email/i)
                const passwordInput = screen.getByLabelText(/password/i)
                const loginButton = screen.getByRole('button', { name: /login/i })

                // 1. Initially disabled
                expect(loginButton).toBeDisabled()

                // 2. Clear and enter valid email, invalid password (e.g., too short)
                await userEvent.clear(emailInput);
                await userEvent.clear(passwordInput);
                await userEvent.type(emailInput, 'karan@gmail.com');
                await userEvent.type(passwordInput, '123'); // Short password
                expect(loginButton).toBeDisabled();

                // 3. Clear password, enter valid password
                await userEvent.clear(passwordInput);
                await userEvent.type(passwordInput, 'Karan123');
                expect(loginButton).toBeEnabled();

                // 4. Clear email, password filled => disabled
                await userEvent.clear(emailInput);
                expect(loginButton).toBeDisabled();

                // 5. Fill valid email again => enabled
                await userEvent.type(emailInput, 'karan@gmail.com');
                expect(loginButton).toBeEnabled();

                // 6. Empty both fields again => disabled
                await userEvent.clear(emailInput);
                await userEvent.clear(passwordInput);
                expect(loginButton).toBeDisabled();
        }, 10000)
})

describe('Login', () => {
        it('submits login and navigates on success', async () => {
                server.use(
                        http.post('http://localhost:8502/api/login', () => {
                                return new HttpResponse(null, { status: 200 })
                        })
                )

                render(
                        <BrowserRouter>
                                <Login />
                        </BrowserRouter>
                )

                const emailInput = screen.getByLabelText(/email/i)
                const passwordInput = screen.getByLabelText(/password/i)
                const loginButton = screen.getByRole('button', { name: /login/i })

                await userEvent.type(emailInput, 'test@example.com')
                await userEvent.type(passwordInput, 'password123')

                await waitFor(() => {
                        expect(loginButton).toBeEnabled()
                })

                await userEvent.click(loginButton)

                await waitFor(() => {
                        expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
                })
        }, 10000)
})

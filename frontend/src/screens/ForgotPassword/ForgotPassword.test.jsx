import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ForgotPassword from './ForgotPassword'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom')
        return {
                ...actual,
                useNavigate: () => mockNavigate,
        }
})

describe('ForgotPassword Component', () => {
        const validEmail = 'user@example.com'
        const wrongEmail = 'wrong@example.com'
        const securityQuestion = "What's your pet's name?"
        const securityAnswer = 'fluffy'
        const newPassword = 'newPassword123'

        it('fetches and displays security question on valid email', async () => {
                render(
                        <MemoryRouter initialEntries={["/forgotpassword"]}>
                                <Routes>
                                <Route path="/forgotpassword" element={<ForgotPassword />} />
                                </Routes>
                        </MemoryRouter>
                )

                const emailInput = screen.getByPlaceholderText(/enter your email here/i)
                const submitButton = screen.getByRole('button', { name: /submit/i })
                await userEvent.type(emailInput, validEmail)
                await userEvent.click(submitButton)

                await waitFor(() => {
                        expect(screen.getByText(securityQuestion)).toBeInTheDocument()
                })
        })

        it('shows error popover on invalid email', async () => {
                const setErrorText = vi.fn()
                const errorPopoverRef = { current: { showPopover: vi.fn() } }

                render(
                        <MemoryRouter>
                                <ForgotPassword setErrorText={setErrorText} errorPopoverRef={errorPopoverRef} />
                        </MemoryRouter>
                )

                const emailInput = screen.getByPlaceholderText(/enter your email here/i)
                const submitButton = screen.getByRole('button', { name: /submit/i })
                await userEvent.type(emailInput, wrongEmail)
                await userEvent.click(submitButton)

                await waitFor(() => {
                        expect(setErrorText).toHaveBeenCalledWith('Email not found')
                        expect(errorPopoverRef.current.showPopover).toHaveBeenCalled()
                })
        })

        it('verifies answer and allows password reset', async () => {
                render(
                        <MemoryRouter>
                                <ForgotPassword />
                        </MemoryRouter>
                )

                await userEvent.type(screen.getByPlaceholderText(/enter your email here/i), validEmail)
                await userEvent.click(screen.getByRole('button', { name: /submit/i }))
                await waitFor(() => screen.getByText(securityQuestion))

                await userEvent.type(screen.getByPlaceholderText(/answer to the security question/i), securityAnswer)
                await userEvent.click(screen.getByRole('button', { name: /verify/i }))
                await waitFor(() => {
                        expect(screen.getByPlaceholderText(/enter your new password here/i)).toBeInTheDocument()
                })

                await userEvent.type(screen.getByPlaceholderText(/enter your new password here/i), newPassword)
                await userEvent.click(screen.getByRole('button', { name: /reset password/i }))

                await waitFor(() => {
                        expect(mockNavigate).toHaveBeenCalledWith('/login')
                })
        })

        it('handles wrong security answer', async () => {
                const setErrorText = vi.fn()
                const errorPopoverRef = { current: { showPopover: vi.fn() } }

                render(
                        <MemoryRouter>
                                <ForgotPassword setErrorText={setErrorText} errorPopoverRef={errorPopoverRef} />
                        </MemoryRouter>
                )

                await userEvent.type(screen.getByPlaceholderText(/enter your email here/i), validEmail)
                await userEvent.click(screen.getByRole('button', { name: /submit/i }))
                await waitFor(() => screen.getByText(securityQuestion))

                await userEvent.type(screen.getByPlaceholderText(/answer to the security question/i), 'wrong')
                await userEvent.click(screen.getByRole('button', { name: /verify/i }))

                await waitFor(() => {
                        expect(setErrorText).toHaveBeenCalledWith('Incorrect answer')
                        expect(errorPopoverRef.current.showPopover).toHaveBeenCalled()
                })
        })
})

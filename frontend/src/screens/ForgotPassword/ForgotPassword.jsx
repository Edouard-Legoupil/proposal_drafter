import './ForgotPassword.css'

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import downarrow from "../../assets/images/downarrow.svg"
import show from "../../assets/images/login_showPassword.svg"
import hide from "../../assets/images/login_hidePassword.svg"

export default function ForgotPassword (props)
{
        const navigate = useNavigate()

        const [email, setEmail] = useState("")

        async function handleEmailSubmitClick ()
        {
                setLoading(true)

                try
                {
                        const response = await fetch(`${API_BASE_URL}/get-security-question`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ email }),
                        })

                        if(response.ok)
                        {
                                const data = await response.json()
                                setSecurityQuestion(data.question)
                        }
                        else
                        {
                                const data = await response.json()

                                props?.setErrorText(data.error || "Submit failed. Try again.")
                                props?.errorPopoverRef.current.showPopover()
                        }
                }
                catch(error)
                {
                        props?.setErrorText("Error occured. Try again.")
                        props?.errorPopoverRef.current.showPopover()
                }
                finally
                {
                        setLoading(false)
                }
        }

        const [securityQuestion, setSecurityQuestion] = useState("")
        const [securityAnswer, setSecurityAnswer] = useState("")

        const [isVerified, setIsVerified] = useState(false)
        async function handleVerifyClick ()
        {
                setLoading(true)

                const response = await fetch(`${API_BASE_URL}/verify-security-answer`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                email,
                                security_question: securityQuestion,
                                security_answer: securityAnswer.trim().toLowerCase()
                        })
                })

                if(response.ok)
                {
                        setIsVerified(true)
                }
                else
                {
                        const data = await response.json()

                        props?.setErrorText(data.error || "Verification failed. Try again.")
                        props?.errorPopoverRef.current.showPopover()

                        setSecurityQuestion("")
                        setSecurityAnswer("")
                }

                setLoading(false)
        }

        const [loading, setLoading] = useState(false)

        const [password, setPassword] = useState("")
        const [showPassword, setShowPassword] = useState(false)
        async function handleResetPasswordSubmit ()
        {
                setLoading(true)

                const response = await fetch(`${API_BASE_URL}/update-password`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                email,
                                security_question: securityQuestion,
                                security_answer: securityAnswer.trim().toLowerCase(),
                                new_password: password
                        }),
                        credentials: 'include'
                })

                if(response.ok)
                {
                        navigate("/login")
                }
        }

        function handleBackClick ()
        {
                if(!securityQuestion)
                        navigate("/login")
                if(securityQuestion && !isVerified)
                        navigate("/forgotpassword")
                if(securityQuestion && isVerified)
                        navigate("/login")
        }

        return  <form className='Login-form'>
                <button className="ForgotPassword_back" onClick={handleBackClick} data-testid="back-button">
                        <img src={downarrow} alt="Back" />
                        Back
                </button>

                {!securityQuestion ?
                        <>
                                <label className='Login-label' htmlFor='Login_emailInput'>Email</label>
                                <input
                                        type="email"
                                        id="Login_emailInput"
                                        value={email}
                                        placeholder='Enter your email here'
                                        onChange={e => /^[a-zA-Z0-9@._%+-]*$/.test(e.target.value) && setEmail(e.target.value.toLowerCase())}
                                        data-testid="email-input"
                                />

                                <button
                                        type='button'
                                        className="Login-submit Register-submit"
                                        disabled={!email}
                                        onClick={handleEmailSubmitClick}
                                        data-testid="submit-email-button"
                                >
                                        {loading ? "SUBMITTING" : "SUBMIT"}
                                        {loading ? <span className='submitButtonSpinner' /> : ""}
                                </button>
                        </>
                        :
                        ""
                }

                {securityQuestion && !isVerified ?
                        <>
                                <label className='Login-label' htmlFor='Login_securityQuestionInput'>{securityQuestion}</label>

                                <label className='Login-label' htmlFor='Login_securityAnswer'>Answer</label>
                                <input
                                        type="text"
                                        id="Login_securityAnswer"
                                        value={securityAnswer}
                                        placeholder="Answer to the security question"
                                        onChange={e => setSecurityAnswer(e.target.value)}
                                        data-testid="security-answer-input"
                                />

                                <button
                                        type='button'
                                        className="Login-submit Register-submit"
                                        disabled={!securityAnswer}
                                        onClick={handleVerifyClick}
                                        data-testid="verify-button"
                                >
                                        {loading ? "VERIFYING" : "VERIFY"}
                                        {loading ? <span className='submitButtonSpinner' /> : ""}
                                </button>
                        </>
                        :
                        ""
                }

                {email && isVerified ?
                        <>
                                <label className='Login-label' htmlFor='Login_passwordInput'>New password</label>
                                <input
                                        type={showPassword ? 'text' : 'password'}
                                        id="Login_passwordInput"
                                        className='Login_inputPassword'
                                        value={password}
                                        placeholder='Enter your new password here'
                                        onChange={e => setPassword(e.target.value)}
                                        data-testid="password-input"
                                />
                                {password ? <div className="Login_showPasswordToggleContainer">
                                        <img className='Login_passwordShowToggle' src={showPassword ? hide : show} onClick={() => setShowPassword(p => !p)} data-testid="show-password-toggle"/>
                                </div> : ""}

                                <button
                                        type='button'
                                        className="Login-submit Register-submit"
                                        disabled={password.length < 8}
                                        onClick={handleResetPasswordSubmit}
                                        data-testid="reset-password-button"
                                >
                                        {loading ? "RESETTING PASSWORD" : "RESET PASSWORD"}
                                        {loading ? <span className='submitButtonSpinner' /> : ""}
                                </button>
                        </>
                        :
                        ""
                }
        </form>
}
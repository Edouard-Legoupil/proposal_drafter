import './Login.css'

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import ForgotPassword from '../ForgotPassword/ForgotPassword'
import CommonButton from '../../components/CommonButton/CommonButton'
import ResponsiveIllustration from '../../components/ResponsiveIllustration/ResponsiveIllustration'
import OSSFooter from '../../components/OSSFooter/OSSFooter'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import logo from "../../assets/images/App_logo.svg"
import show from "../../assets/images/login_showPassword.svg"
import hide from "../../assets/images/login_hidePassword.svg"

export default function Login (props)
{
        const navigate = useNavigate()

        const errorPopover = useRef()
        const [errorText, setErrorText] = useState("")
        useEffect(() => {
                const sessionExpiredError = sessionStorage.getItem("session_expired")
                if(sessionExpiredError && errorPopover.current.showPopover) {
                        setErrorText(sessionExpiredError)
                        errorPopover.current.showPopover()
                        sessionStorage.removeItem("session_expired")
                }
        }, [])

        const [username, setUsername] = useState("")

        const [email, setEmail] = useState("")

        const [password, setPassword] = useState("")
        const [showPassword, setShowPassword] = useState(false)

        const [securityQuestion, setSecurityQuestion] = useState("")
        const [securityAnswer, setSecurityAnswer] = useState("")

        const [submitButtonText, setSubmitButtonText] = useState(props?.register ? "REGISTER" : "LOGIN")
        const [loading, setLoading] = useState(false)

        useEffect(() => {
                if(errorPopover.current?.hidePopover && password) {
                        setErrorText("")
                        errorPopover.current.hidePopover()
                }
                else
                        setShowPassword(false)
        }, [email, password])

        async function handleLoginClick (e)
        {
                e.preventDefault()

                setSubmitButtonText("LOGGING IN")
                setLoading(true)

                const response = await fetch(`${API_BASE_URL}/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password }),
                        credentials: 'include'
                })

                if (response.ok)
                {
                        navigate("/dashboard")
                }
                else
                {
                        setSubmitButtonText(props?.register ? "REGISTER" : "LOGIN")
                        setLoading(false)

                        const data = await response.json() ?? { error: "Login failed! Please try again." }

                        setPassword("")
                        setShowPassword(false)
                        if(errorPopover.current.showPopover)
                                errorPopover.current.showPopover()
                        setErrorText(data.error)
                }
        }

        async function handleRegisterClick (e)
        {
                setSubmitButtonText("REGISTERING")
                setLoading(true)

                e.preventDefault()

                const response = await fetch(`${API_BASE_URL}/signup`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                username,
                                email,
                                password,
                                security_question: securityQuestion,
                                security_answer: securityAnswer.trim().toLowerCase()
                        })
                })

                if (response.ok)
                        handleLoginClick(e)
                else
                {
                        setSubmitButtonText("REGISTER")
                        setLoading(false)

                        const data = await response.json()

                        errorPopover.current.showPopover()
                        setErrorText(data.error || "Signup failed!")

                        setUsername("")
                        setEmail("")
                        setPassword("")
                        setSecurityQuestion("")
                        setSecurityAnswer("")
                        setShowPassword(false)
                }
        }

        return  <div className="Login_container">
                <div className='Login'>
                        <div popover="auto" className='Login-errorPopover' ref={errorPopover}>
                                <span>🛇 {errorText}</span>
                                <span onClick={() => errorPopover.current.hidePopover()} style={{ cursor: "pointer" }}>✖</span>
                        </div>
                        <div className='Login-left'>
                                <div className="Login-appLogo">
                                        <img className='Login-logo' src={logo} alt='My Rafiki logo' />
                                </div>
                                {props?.forgotPassword ?
                                        <ForgotPassword errorPopoverRef={errorPopover} setErrorText={setErrorText} />
                                        :
                                        <form className='Login-form' onSubmit={props?.register ? handleRegisterClick : handleLoginClick}>
                                                <h3 className='Login_form-header'>{props?.register ? "Register" : "Login"}</h3>
                                                {props?.register ?
                                                        <>
                                                                <label className='Login-label' htmlFor='Login_nameInput'>Name</label>
                                                                <input
                                                                        type="text"
                                                                        id='Login_nameInput'
                                                                        value={username}
                                                                        placeholder='Your name'
                                                                        onChange={e => /^[A-Za-z\s]{0,16}$/.test(e.target.value) && setUsername(e.target.value)}
                                                                />
                                                        </>
                                                        :
                                                        ""
                                                }
                                                <label className='Login-label' htmlFor='Login_emailInput'>Email</label>
                                                <input
                                                        type="email"
                                                        id="Login_emailInput"
                                                        value={email}
                                                        placeholder={props?.register ? 'example@email.com' : 'Enter your email here'}
                                                        onChange={e => /^[a-zA-Z0-9@._%+-]*$/.test(e.target.value) && setEmail(e.target.value.toLowerCase())}
                                                />
                                                <label className='Login-label' htmlFor='Login_passwordInput'>Password</label>
                                                <input
                                                        type={showPassword ? 'text' : 'password'}
                                                        id="Login_passwordInput"
                                                        className='Login_inputPassword'
                                                        value={password}
                                                        placeholder={props?.register ? 'At least 8 characters' : 'Enter your password here'}
                                                        onChange={e => setPassword(e.target.value)}
                                                        autoComplete="current-password"
                                                />
                                                {password ? <div className="Login_showPasswordToggleContainer">
                                                        <img className='Login_passwordShowToggle' src={showPassword ? hide : show} onClick={() => setShowPassword(p => !p)}/>
                                                </div> : ""}
                                                {props?.register ?
                                                        <>
                                                                <label className='Login-label' htmlFor='Login_securityQuestionInput'>Security Question</label>
                                                                <select
                                                                        id="Login_securityQuestionInput"
                                                                        value={securityQuestion}
                                                                        onChange={e => setSecurityQuestion(e.target.value)}
                                                                        style={securityQuestion === "" ? {color: "rgb(117, 117, 117)"} : {}}
                                                                >
                                                                        <option value="" disabled>Select security question</option>
                                                                        <option>Favourite animal?</option>
                                                                        <option>Favourite sport?</option>
                                                                        <option>Favourite movie?</option>
                                                                        <option>Favourite song?</option>
                                                                </select>
                                                                <label className='Login-label' htmlFor='Login_securityAnswer'>Answer</label>
                                                                <input
                                                                        type="text"
                                                                        id="Login_securityAnswer"
                                                                        value={securityAnswer}
                                                                        placeholder="Answer to the security question"
                                                                        onChange={e => setSecurityAnswer(e.target.value)}
                                                                />
                                                        </>
                                                        :
                                                        ""
                                                }
                                                {!props?.register ? <a href='/forgotpassword' className='Login-forgotpw'>Forgot Password?</a> : ""}
                                                <CommonButton
                                                        type="submit"
                                                        disabled={(props?.register && !username) || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length >= 255 || password.length < 8 || (props?.register && !securityAnswer)}
                                                        label={submitButtonText}
                                                        loading={loading}
                                                        style={{ marginTop: "20px" }}
                                                />
                                                <div className='Login-register'>
                                                        {props?.register ?
                                                                <>
                                                                        Already have an account?
                                                                        <a href="/login"> Log in</a>
                                                                </>
                                                                :
                                                                <>
                                                                        Don't have an account?
                                                                        <a href="/register"> Sign up</a>
                                                                </>
                                                        }
                                                </div>
                                        </form>
                                }
                        </div>
                        <div className="Login-rightIllustration">
                                <ResponsiveIllustration />
                        </div>
                </div>

                <OSSFooter />
        </div>
}

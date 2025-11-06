import './Login.css'

import { useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faWandMagicSparkles, faDatabase, faUsers } from '@fortawesome/free-solid-svg-icons'
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

        const [teamId, setTeamId] = useState("")
        const [teams, setTeams] = useState([])
        const [securityQuestion, setSecurityQuestion] = useState("")
        const [securityAnswer, setSecurityAnswer] = useState("")
        const [acknowledged, setAcknowledged] = useState(false)

        useEffect(() => {
                async function fetchTeams() {
                        try {
                                const response = await fetch(`${API_BASE_URL}/teams`);
                                if (response.ok) {
                                        const data = await response.json();
                                        setTeams(data.teams);
                                }
                        } catch (error) {
                                console.error("Failed to fetch teams:", error);
                        }
                }
                if (props?.register) {
                        fetchTeams();
                }
        }, [props?.register]);

        const [submitButtonText, setSubmitButtonText] = useState(props?.register ? "REGISTER" : "LOGIN")
        const [loading, setLoading] = useState(false)
        const [ssoEnabled, setSsoEnabled] = useState(false)

        useEffect(() => {
                async function fetchSsoStatus() {
                        try {
                                const response = await fetch(`${API_BASE_URL}/sso-status`);
                                if (response.ok) {
                                        const data = await response.json();
                                        setSsoEnabled(data.enabled);
                                }
                        } catch (error) {
                                console.error("Failed to fetch SSO status:", error);
                        }
                }
                fetchSsoStatus();
        }, []);

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
                                team_id: teamId,
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
                        setTeamId("")
                        setSecurityQuestion("")
                        setSecurityAnswer("")
                        setShowPassword(false)
                }
        }

        return  <div className="Login_container" data-testid="login-container">
                <div className='Login'>
                        <div popover="auto" className='Login-errorPopover' ref={errorPopover} data-testid="error-popover">
                                <span>🛇 {errorText}</span>
                                <span onClick={() => errorPopover.current.hidePopover()} style={{ cursor: "pointer" }} data-testid="error-popover-close">✖</span>
                        </div>
                        <div className='Login-left'>
                                <div className="Login-appLogo">
                                        <img className='Login-logo' src={logo} alt='Proposal Gen logo' />
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
                                                                        data-testid="name-input"
                                                                />
                                                                <label className='Login-label' htmlFor='Login_teamInput'>Team</label>
                                                                <select
                                                                    id="Login_teamInput"
                                                                    value={teamId}
                                                                    onChange={e => setTeamId(e.target.value)}
                                                                    required
                                                                    data-testid="team-select"
                                                                >
                                                                    <option value="" disabled>Select your team</option>
                                                                    {teams.map(team => (
                                                                        <option key={team.id} value={team.id}>{team.name}</option>
                                                                    ))}
                                                                </select>
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
                                                        data-testid="email-input"
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
                                                        data-testid="password-input"
                                                />
                                                {password ? <div className="Login_showPasswordToggleContainer">
                                                        <img className='Login_passwordShowToggle' src={showPassword ? hide : show} onClick={() => setShowPassword(p => !p)} data-testid="show-password-toggle"/>
                                                </div> : ""}
                                                {props?.register ?
                                                        <>
                                                                <label className='Login-label' htmlFor='Login_securityQuestionInput'>Security Question</label>
                                                                <select
                                                                        id="Login_securityQuestionInput"
                                                                        value={securityQuestion}
                                                                        onChange={e => setSecurityQuestion(e.target.value)}
                                                                        style={securityQuestion === "" ? {color: "rgb(117, 117, 117)"} : {}}
                                                                        data-testid="security-question-select"
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
                                                                        data-testid="security-answer-input"
                                                                />
                                                                <div style={{ display: 'flex', alignItems: 'flex-start', marginTop: '15px', gap: '10px' }}>
                                                                        <input
                                                                                type="checkbox"
                                                                                id="Login_acknowledgement"
                                                                                checked={acknowledged}
                                                                                onChange={e => setAcknowledged(e.target.checked)}
                                                                                required
                                                                                data-testid="acknowledgement-checkbox"
                                                                                style={{ marginTop: '4px' }}
                                                                        />
                                                                        <label htmlFor="Login_acknowledgement" style={{ fontSize: '12px', color: 'grey', textAlign: 'left' }}>
                                                                                <p>I acknowledge that this system is intended for UNHCR staff and members of UNHCR national societies.</p>
                                                                                <p>I understand that AI-generated content may contain inaccuracies or "hallucinations," and I commit to carefully reviewing all generated materials before use.</p>
                                                                                <p>I will use this tool responsibly, mindful of the financial and environmental resources it consumes.</p>
                                                                        </label>
                                                                </div>
                                                        </>
                                                        :
                                                        ""
                                                }
                                                {!props?.register ? <a href='/forgotpassword' className='Login-forgotpw' data-testid="forgot-password-link">Forgot Password?</a> : ""}
                                                <CommonButton
                                                        type="submit"
                                                        disabled={(props?.register && !username) || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length >= 255 || password.length < 8 || (props?.register && !securityAnswer) || (props?.register && !acknowledged)}
                                                        label={submitButtonText}
                                                        loading={loading}
                                                        style={{ marginTop: "20px" }}
                                                        data-testid="submit-button"
                                                />
                                                <div className='Login-register'>
                                                        {props?.register ?
                                                                <>
                                                                        Already have an account?
                                                                        <a href="/login" data-testid="login-link"> Log in</a>
                                                                </>
                                                                :
                                                                <>
                                                                        {ssoEnabled && (
                                                                                <>
                                                                                        <CommonButton
                                                                                                label="LOGIN WITH MICROSOFT"
                                                                                                onClick={() => window.location.href = `${API_BASE_URL}/sso-login`}
                                                                                                style={{ marginTop: "20px", backgroundColor: "#2F2F2F" }}
                                                                                        />
                                                                                        <div className='Login-divider'>
                                                                                                <hr/>
                                                                                                <span>OR</span>
                                                                                                <hr/>
                                                                                        </div>
                                                                                </>
                                                                        )}
                                                                        Don't have an account?
                                                                        <a href="/register" data-testid="register-link"> Sign up</a>
                                                                </>
                                                        }
                                                </div>
                                        </form>
                                }
                                <div className='Login-motto'>
                                        <div className='Login-motto-item'>
                                                <p className='Login-motto-text'>⚠️ Beta Version for Testing Purpose ⚠️</p>
                                        </div>
                                        <div className='Login-motto-item'>
                                                <FontAwesomeIcon icon={faWandMagicSparkles} className='Login-motto-icon' />
                                                <p className='Login-motto-text'>Draft Initial Project Proposal with AI</p>
                                        </div>
                                        <div className='Login-motto-item'>
                                                <FontAwesomeIcon icon={faDatabase} className='Login-motto-icon' />
                                                <p className='Login-motto-text'>Leverage Curated Knowledge on Donors, Field Context and Interventions</p>
                                        </div>
                                        <div className='Login-motto-item'>
                                                <FontAwesomeIcon icon={faUsers} className='Login-motto-icon' />
                                                <p className='Login-motto-text'>Organize Peer Review for Continuous Learning</p>
                                        </div>
                                </div>
                                <div style={{ marginTop: '20px', fontSize: '12px', color: 'grey', textAlign: 'center' }}>
                                    <p>You are now running <a href="https://github.com/Edouard-Legoupil/proposal_drafter/releases/tag/0.4" target="_blank" rel="noopener noreferrer">v.0.4</a></p>
                                </div>
                        </div>
                </div>

                <OSSFooter />
        </div>
}

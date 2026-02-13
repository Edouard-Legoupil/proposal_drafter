import './Login.css'

import { useEffect, useRef, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faWandMagicSparkles, faDatabase, faUsers } from '@fortawesome/free-solid-svg-icons'
import { useNavigate } from 'react-router-dom'
import Select from 'react-select'

import ForgotPassword from '../ForgotPassword/ForgotPassword'
import CommonButton from '../../components/CommonButton/CommonButton'
import ResponsiveIllustration from '../../components/ResponsiveIllustration/ResponsiveIllustration'
import OSSFooter from '../../components/OSSFooter/OSSFooter'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

import logo from "../../assets/images/App_logo.svg"
import show from "../../assets/images/login_showPassword.svg"
import hide from "../../assets/images/login_hidePassword.svg"

export default function Login(props) {
        const navigate = useNavigate()

        const errorPopover = useRef()
        const [errorText, setErrorText] = useState("")
        useEffect(() => {
                const sessionExpiredError = sessionStorage.getItem("session_expired")
                if (sessionExpiredError && errorPopover.current.showPopover) {
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

        const [roles, setRoles] = useState([])
        const [selectedRoles, setSelectedRoles] = useState([])
        const [donorGroups, setDonorGroups] = useState([])
        const [selectedDonorGroups, setSelectedDonorGroups] = useState([])
        const [outcomes, setOutcomes] = useState([])
        const [selectedOutcomes, setSelectedOutcomes] = useState([])
        const [geographicCoverageType, setGeographicCoverageType] = useState("global")
        const [geographicCoverageRegion, setGeographicCoverageRegion] = useState("")
        const [geographicCoverageCountry, setGeographicCoverageCountry] = useState("")


        useEffect(() => {
                async function fetchFormData() {
                        try {
                                const [teamsRes, rolesRes, donorGroupsRes, outcomesRes] = await Promise.all([
                                        fetch(`${API_BASE_URL}/teams`),
                                        fetch(`${API_BASE_URL}/roles`),
                                        fetch(`${API_BASE_URL}/donors/groups`),
                                        fetch(`${API_BASE_URL}/outcomes`)
                                ]);

                                if (teamsRes.ok) {
                                        const data = await teamsRes.json();
                                        setTeams(data.teams);
                                }
                                if (rolesRes.ok) {
                                        const data = await rolesRes.json();
                                        setRoles(data.map(r => ({ value: r.id, label: r.name })));
                                }
                                if (donorGroupsRes.ok) {
                                        const data = await donorGroupsRes.json();
                                        setDonorGroups(data.donor_groups.map(dg => ({ value: dg, label: dg })));
                                }
                                if (outcomesRes.ok) {
                                        const data = await outcomesRes.json();
                                        setOutcomes(data.outcomes.map(o => ({ value: o.id, label: o.name })));
                                }
                        } catch (error) {
                                console.error("Failed to fetch form data:", error);
                        }
                }
                if (props?.register) {
                        fetchFormData();
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
                if (errorPopover.current?.hidePopover && password) {
                        setErrorText("")
                        errorPopover.current.hidePopover()
                }
                else
                        setShowPassword(false)
        }, [email, password])

        async function handleLoginClick(e) {
                e.preventDefault()

                setSubmitButtonText("LOGGING IN")
                setLoading(true)

                const response = await fetch(`${API_BASE_URL}/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ identifier: email, password }),
                        credentials: 'include'
                })

                if (response.ok) {
                        navigate("/dashboard")
                }
                else {
                        setSubmitButtonText(props?.register ? "REGISTER" : "LOGIN")
                        setLoading(false)

                        const data = await response.json() ?? { error: "Login failed! Please try again." }

                        setPassword("")
                        setShowPassword(false)
                        if (errorPopover.current.showPopover)
                                errorPopover.current.showPopover()
                        setErrorText(data.error)
                }
        }

        async function handleRegisterClick(e) {
                setSubmitButtonText("REGISTERING")
                setLoading(true)

                e.preventDefault()

                const settings = {
                        geographic_coverage_type: geographicCoverageType,
                        geographic_coverage_region: geographicCoverageRegion,
                        geographic_coverage_country: geographicCoverageCountry,
                        roles: selectedRoles.map(r => r.value),
                        donor_groups: selectedDonorGroups.map(dg => dg.value),
                        outcomes: selectedOutcomes.map(o => o.value)
                }

                const response = await fetch(`${API_BASE_URL}/signup`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                                username,
                                email,
                                password,
                                team_id: teamId,
                                security_question: securityQuestion,
                                security_answer: securityAnswer.trim().toLowerCase(),
                                settings
                        })
                })

                if (response.ok)
                        handleLoginClick(e)
                else {
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

        return <div className="Login_container" data-testid="login-container">
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
                                                {!props?.register && ssoEnabled && (
                                                        <>
                                                                <CommonButton
                                                                        label="LOG IN USING UNHCR SSO"
                                                                        onClick={() => window.location.href = `${API_BASE_URL}/sso-login`}
                                                                        className="Login-ssoButton"
                                                                        style={{ marginTop: "10px" }}
                                                                />
                                                                <div style={{ fontSize: '12px', color: '#666', textAlign: 'center', marginTop: '16px', marginBottom: '8px' }}>
                                                                        Having trouble accessing SSO? <a href="mailto:legoupil@unhcr.org?subject=Access%20Proposal%20Gen" style={{ color: '#0072BC', textDecoration: 'underline' }}>Request access</a>
                                                                </div>
                                                                <div className='Login_divider' style={{ margin: "16px 0" }}>
                                                                        <hr />
                                                                        <span>OR</span>
                                                                        <hr />
                                                                </div>
                                                        </>
                                                )}
                                                <label className='Login-label' htmlFor='Login_identifierInput'>Username or Email</label>
                                                <input
                                                        type="text"
                                                        id="Login_identifierInput"
                                                        value={email}
                                                        placeholder={props?.register ? 'example@email.com' : 'Enter your username or email'}
                                                        onChange={e => setEmail(e.target.value)}
                                                        data-testid="identifier-input"
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
                                                        <img className='Login_passwordShowToggle' src={showPassword ? hide : show} onClick={() => setShowPassword(p => !p)} data-testid="show-password-toggle" />
                                                </div> : ""}
                                                {props?.register ?
                                                        <>
                                                                <label className='Login-label'>Roles</label>
                                                                <Select
                                                                        isMulti
                                                                        options={roles}
                                                                        value={selectedRoles}
                                                                        onChange={setSelectedRoles}
                                                                />

                                                                {selectedRoles.some(r => r.label === 'knowledge manager donors') && (
                                                                        <>
                                                                                <label className='Login-label'>Donor Groups</label>
                                                                                <Select
                                                                                        isMulti
                                                                                        options={donorGroups}
                                                                                        value={selectedDonorGroups}
                                                                                        onChange={setSelectedDonorGroups}
                                                                                />
                                                                        </>
                                                                )}

                                                                {selectedRoles.some(r => r.label === 'knowledge manager outcome') && (
                                                                        <>
                                                                                <label className='Login-label'>Outcomes</label>
                                                                                <Select
                                                                                        isMulti
                                                                                        options={outcomes}
                                                                                        value={selectedOutcomes}
                                                                                        onChange={setSelectedOutcomes}
                                                                                />
                                                                        </>
                                                                )}

                                                                <label className='Login-label'>Geographic Coverage</label>
                                                                <select value={geographicCoverageType} onChange={e => setGeographicCoverageType(e.target.value)}>
                                                                        <option value="global">Global</option>
                                                                        <option value="regional">Regional</option>
                                                                        <option value="country">Country</option>
                                                                </select>

                                                                {geographicCoverageType === 'regional' && (
                                                                        <input type="text" placeholder="Region" value={geographicCoverageRegion} onChange={e => setGeographicCoverageRegion(e.target.value)} />
                                                                )}
                                                                {geographicCoverageType === 'country' && (
                                                                        <input type="text" placeholder="Country" value={geographicCoverageCountry} onChange={e => setGeographicCoverageCountry(e.target.value)} />
                                                                )}
                                                                <label className='Login-label' htmlFor='Login_securityQuestionInput'>Security Question</label>
                                                                <select
                                                                        id="Login_securityQuestionInput"
                                                                        value={securityQuestion}
                                                                        onChange={e => setSecurityQuestion(e.target.value)}
                                                                        style={securityQuestion === "" ? { color: "rgb(117, 117, 117)" } : {}}
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
                                                        disabled={(props?.register && !username) || (props?.register ? !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) : !email) || email.length >= 255 || password.length < 8 || (props?.register && !securityAnswer) || (props?.register && !acknowledged)}
                                                        label={submitButtonText}
                                                        loading={loading}
                                                        style={{ marginTop: "10px" }}
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
                                        <p>You are now running <a href="https://github.com/Edouard-Legoupil/proposal_drafter/releases/tag/0.6" target="_blank" rel="noopener noreferrer">v.0.6</a></p>
                                </div>
                        </div>
                </div>

                <OSSFooter />
        </div>
}

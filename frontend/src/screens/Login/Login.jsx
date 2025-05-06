import './Login.css'

import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import ResponsiveIllustration from '../../components/ResponsiveIllustration/ResponsiveIllustration'

import logo from "../../assets/images/App_logo.svg"
import CommonButton from '../../components/CommonButton/CommonButton'

export default function Login (props)
{
        const navigate = useNavigate()

        const errorPopover = useRef()

        const [email, setEmail] = useState("")
        const [errorText, setErrorText] = useState("")

        const [loading, setLoading] = useState(false)
        async function handleLoginClick (e)
        {
                e.preventDefault()

                setLoading(true)

                // const response = await fetch('http://192.168.157.40:8501/login', {
                //         method: 'POST',
                //         headers: { 'Content-Type': 'application/json' },
                //         body: JSON.stringify({ email }),
                //         credentials: 'include'
                // })

                // if (response.ok) {
                //         console.log("response.ok")
                //         navigate("/dashboard")
                // }
                // else
                // {
                //         const data = await response.json()
                //         errorPopover.current.showPopover()
                //         setErrorText(data.error || "Login failed!")
                // }

                window.location.href = "/dashboard"
        }

        return  <div className='Login'>
                <div popover="auto" className='Login-errorPopover' ref={errorPopover}>
                        <span>🛇 {errorText}</span>
                        <span onClick={() => errorPopover.current.hidePopover()}>✖</span>
                </div>

                <div className='Login-left'>
                        <div className="Login-appLogo">
                                <img className='Login-logo' src={logo} alt='My Rafiki logo' />
                        </div>

                        <form className='Login-form' onSubmit={handleLoginClick}>
                                <h3 className='Login_form-header'>LOGIN</h3>
                                <div className='Login-label'>Email</div>
                                <input
                                        type="email"
                                        value={email}
                                        placeholder='Enter your email here'
                                        onChange={e => /^[a-zA-Z0-9@._%+-]*$/.test(e.target.value) && setEmail(e.target.value.toLowerCase())}
                                />

                                <button
                                        type='submit'
                                        className="Login-submit"
                                        disabled={!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)}
                                >
                                        {loading ?
                                                <>
                                                        LOGGING IN
                                                        <span className='submitButtonSpinner' />
                                                </>
                                                :
                                                <>
                                                        LOGIN WITH SSO
                                                </>
                                        }
                                </button>

                                {/* <CommonButton type="submit" disabled={!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)} label="LOGIN WITH SSO" loading={loading} loadingLabel="LOGGING IN" /> */}
                        </form>
                </div>

                <div className="Login-rightIllustration">
                        <ResponsiveIllustration />
                </div>
        </div>
}

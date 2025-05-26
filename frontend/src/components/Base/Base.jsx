import './Base.css'

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import masterlogo from '../../assets/images/App_invertedLogo.svg'

import downarrow from "../../assets/images/downarrow.svg"
import logout_icon from "../../assets/images/Header_logout.svg"

export default function Base (props)
{
        const navigate = useNavigate()

        const [userDetails, setUserDetails] = useState({
                "name": "",
                "email": ""
        })

        function handleLogoClick ()
        {
                navigate("/dashboard")
        }

        useEffect(() => {
                async function getProfile()
                {
                        const response = await fetch(`${API_BASE_URL}/profile`, {
                                method: 'GET',
                                headers: { 'Content-Type': 'application/json' },
                                credentials: 'include'
                        })

                        if (response.ok) {
                                const data = await response.json()
                                setUserDetails({
                                        name: data.user.name,
                                        email: data.user.email
                                })
                        }
                        else if(response.status === 401)
                        {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                        else
                                navigate("/login")
                }

                getProfile()
        }, [navigate])

        async function handleLogoutClick ()
        {
                try
                {
                        const response = await fetch(`${API_BASE_URL}/logout`, {
                                method: "POST",
                                credentials: "include",
                                headers: { "Content-Type": "application/json" }
                        })

                        if(response)
                                navigate("/login")
                }
                catch(error)
                {
                        console.log(error)
                        navigate("/login")
                }
        }

        return  <div className='Base'>
                <header className='Header'>
                        <span className='Header_logoContainer'>
                                <img className='Header_iomLogo' src={masterlogo} onClick={handleLogoClick} alt="IOM - UN Migration" />
                        </span>

                        <button className='User' popoverTarget='ID_Chat_logoutPopover'>
                                <div className="Displaypicture">{userDetails.name && userDetails.name.split('')[0].toUpperCase()}</div>

                                <div className='Identity'>
                                        <div className='Identity-name'>{userDetails.name}</div>
                                        <div className='Identity-email'>{userDetails.email}</div>
                                </div>

                                <img className="Chat_header_downarrow" src={downarrow} alt="My Rafiki"/>

                        </button>

                        <div popover='auto' id="ID_Chat_logoutPopover" className='Chat_logoutPopover' onClick={handleLogoutClick}>
                                <img src={logout_icon} />
                                Logout
                        </div>
                </header>

                <main className='Main'>
                        {props?.children}
                </main>
        </div>
}
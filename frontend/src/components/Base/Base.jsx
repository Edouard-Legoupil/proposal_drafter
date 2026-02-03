import './Base.css'

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import OSSFooter from '../OSSFooter/OSSFooter'
import UserSettingsModal from '../UserSettingsModal/UserSettingsModal'
import UserAdminModal from '../UserAdminModal/UserAdminModal'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL

import masterlogo from '../../assets/images/App_invertedLogo.svg'
import downarrow from "../../assets/images/downarrow.svg"
import logout_icon from "../../assets/images/Header_logout.svg"
import settings_icon from "../../assets/images/dashboard-category.svg"

export default function Base(props) {
        const navigate = useNavigate()

        const [userDetails, setUserDetails] = useState({
                "name": "",
                "email": "",
                "is_admin": false
        })
        const [showSettingsModal, setShowSettingsModal] = useState(false)
        const [showAdminModal, setShowAdminModal] = useState(false)

        function handleLogoClick() {
                navigate("/dashboard")
        }

        useEffect(() => {
                async function getProfile() {
                        const response = await fetch(`${API_BASE_URL}/profile`, {
                                method: 'GET',
                                headers: { 'Content-Type': 'application/json' },
                                credentials: 'include'
                        })

                        if (response.ok) {
                                const data = await response.json()
                                setUserDetails({
                                        name: data.user.name,
                                        email: data.user.email,
                                        is_admin: data.user.is_admin
                                })
                        }
                        else if (response.status === 401) {
                                sessionStorage.setItem("session_expired", "Session expired. Please login again.")
                                navigate("/login")
                        }
                        else
                                navigate("/login")
                }

                getProfile()
        }, [navigate])

        async function handleLogoutClick() {
                try {
                        const response = await fetch(`${API_BASE_URL}/logout`, {
                                method: "POST",
                                credentials: "include",
                                headers: { "Content-Type": "application/json" }
                        })

                        if (response)
                                navigate("/login")
                }
                catch (error) {
                        console.log(error)
                        navigate("/login")
                }
        }

        return <div className='Base'>
                <header className='Header'>
                        <span className='Header_logoContainer'>
                                <img className='Header_orgLogo' src={masterlogo} onClick={handleLogoClick} alt="Organisation" data-testid="logo" />
                        </span>

                        <button className='User' popoverTarget='ID_Chat_logoutPopover' data-testid="user-menu-button">
                                <div className="Displaypicture">{userDetails.name && userDetails.name.split('')[0].toUpperCase()}</div>

                                <div className='Identity'>
                                        <div className='Identity-name'>{userDetails.name}</div>
                                        <div className='Identity-email'>{userDetails.email}</div>
                                </div>

                                <img className="Chat_header_downarrow" src={downarrow} alt="My Rafiki" />

                        </button>

                        <div popover='auto' id="ID_Chat_logoutPopover" className='Chat_logoutPopover'>
                                <div onClick={() => setShowSettingsModal(true)} data-testid="settings-button">
                                        <img src={settings_icon} />
                                        Settings
                                </div>
                                {userDetails.is_admin && (
                                        <div onClick={() => setShowAdminModal(true)} data-testid="admin-button">
                                                <img src={settings_icon} style={{ filter: 'hue-rotate(90deg)' }} />
                                                Admin
                                        </div>
                                )}
                                <div onClick={handleLogoutClick} data-testid="logout-button">
                                        <img src={logout_icon} />
                                        Logout
                                </div>
                        </div>
                </header>

                <main className='Main'>
                        {props?.children}
                </main>

                <UserSettingsModal show={showSettingsModal} onClose={() => setShowSettingsModal(false)} />
                <UserAdminModal show={showAdminModal} onClose={() => setShowAdminModal(false)} />

                <OSSFooter />
        </div>
}

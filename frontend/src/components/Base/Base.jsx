import './Base.css'

import { useState } from 'react'

import masterlogo from '../../assets/images/App_invertedLogo.svg'
import dp from '../../assets/images/dp.png'

export default function Base (props) {
        const [userDetails, setUserDetails] = useState({
                "name": "Dylan Sanjay Patel",
                "email": "dylansp@iom.com"
        })

        return  <div className='Base'>
                <header className='Header'>
                        <span className='Header_logoContainer'>
                                <img className='Header_iomLogo' src={masterlogo} alt="IOM - UN Migration" />
                                {/* <img className='Masterlogo' src={logo} alt="IOM - UN Migration" /> */}
                        </span>

                        <div className='User'>
                                <img className='Displaypicture' src={dp} alt="Profile Image" />
                                <div className='Identity'>
                                        <div className='Identity-name'>{userDetails.name}</div>
                                        <div className='Identity-email'>{userDetails.email}</div>
                                </div>
                        </div>
                </header>

                <main className='Main'>
                        {props?.children}
                </main>
        </div>
}
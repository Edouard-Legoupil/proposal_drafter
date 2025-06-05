import { Routes, Route } from 'react-router-dom'

import Login from './screens/Login/Login'
import Dashboard from './screens/Dashboard/Dashboard'
import Chat from './screens/Chat/Chat'

export default function App()
{
        return  <Routes>
                <Route path="/" element={<Login/>} />
                <Route path="/login" element={<Login/>} />
                <Route path="/register" element={<Login register />} />
                <Route path="/forgotpassword" element={<Login forgotPassword/>} />
                <Route path="/dashboard" element={<Dashboard/>} />
                <Route path="/chat" element={<Chat/>} />
        </Routes>
}

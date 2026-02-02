import { Routes, Route } from 'react-router-dom'

import Login from './screens/Login/Login'
import Dashboard from './screens/Dashboard/Dashboard'
import Chat from './screens/Chat/Chat'
import Review from './screens/Review/Review'
import KnowledgeCard from './screens/KnowledgeCard/KnowledgeCard'

export default function App()
{
        return  <Routes>
                <Route path="/" element={<Login/>} />
                <Route path="/login" element={<Login/>} />
                <Route path="/register" element={<Login register />} />
                <Route path="/forgotpassword" element={<Login forgotPassword/>} />
                <Route path="/dashboard" element={<Dashboard/>} />
                <Route path="/dashboard/:folder" element={<Dashboard/>} />
                <Route path="/dashboard/:folder/:subfolder" element={<Dashboard/>} />
                <Route path="/chat" element={<Chat/>} />
                <Route path="/chat/:id" element={<Chat/>} />
                <Route path="/review/:proposal_id" element={<Review />} />
                <Route path="/knowledge-card/new" element={<KnowledgeCard />} />
                <Route path="/knowledge-card/:id" element={<KnowledgeCard />} />
        </Routes>
}

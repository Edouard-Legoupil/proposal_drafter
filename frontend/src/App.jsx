import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'

const Login = lazy(() => import('./screens/Login/Login'))
const Dashboard = lazy(() => import('./screens/Dashboard/Dashboard'))
const Chat = lazy(() => import('./screens/Chat/Chat'))
const Review = lazy(() => import('./screens/Review/Review'))
const KnowledgeCard = lazy(() => import('./screens/KnowledgeCard/KnowledgeCard'))

export default function App()
{
        return  <Suspense fallback={<div></div>}>
                        <Routes>
                                <Route path="/" element={<Login/>} />
                                <Route path="/login" element={<Login/>} />
                                <Route path="/register" element={<Login register />} />
                                <Route path="/forgotpassword" element={<Login forgotPassword/>} />
                                <Route path="/dashboard" element={<Dashboard/>} />
                                <Route path="/chat" element={<Chat/>} />
                                <Route path="/review/:proposal_id" element={<Review />} />
                                <Route path="/knowledge-card/new" element={<KnowledgeCard />} />
                                <Route path="/knowledge-card/:id" element={<KnowledgeCard />} />
                        </Routes>
                </Suspense>
}

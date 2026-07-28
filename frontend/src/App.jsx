import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes } from 'react-router-dom'

import Login from './screens/Login/Login'
import { useAuth } from './context/AuthContext'

const Dashboard = lazy(() => import('./screens/Dashboard/Dashboard'))
const Chat = lazy(() => import('./screens/Chat/Chat'))
const KnowledgeCard = lazy(() => import('./screens/KnowledgeCard/KnowledgeCard'))
const DonorTemplateRequest = lazy(() => import('./screens/DonorTemplateRequest/DonorTemplateRequest'))
const DonorTemplateDetail = lazy(() => import('./screens/DonorTemplateDetail/DonorTemplateDetail'))
const QualityGate = lazy(() => import('./screens/QualityGate/QualityGate'))
const AccessManagement = lazy(() => import('./screens/Admin/AccessManagement'))
const WizardModal = lazy(() => import('./components/Wizard/WizardModal'))
const WizardDebug = lazy(() => import('./components/Wizard/WizardDebug'))

function RequireUser() {
        const { user, loading } = useAuth()
        if (loading) return <div role="status">Checking session…</div>
        return user ? <Outlet /> : <Navigate to="/login" replace />
}

function RequireAdmin() {
        const { user, loading } = useAuth()
        if (loading) return <div role="status">Checking session…</div>
        if (!user) return <Navigate to="/login" replace />
        return user.is_admin ? <Outlet /> : <Navigate to="/dashboard" replace />
}

function RequireRole({ role }) {
        const { user, roles = [], loading } = useAuth()
        if (loading) return <div role="status">Checking session…</div>
        if (!user) return <Navigate to="/login" replace />
        return user.is_admin || roles.includes(role) ? <Outlet /> : <Navigate to="/dashboard" replace />
}

export default function App()
{
        const { user, loading } = useAuth()
        return  (
            <>
                <Suspense fallback={<div role="status" aria-label="Loading page">Loading page…</div>}>
                  <Routes>
                        <Route path="/" element={<Login/>} />
                        <Route path="/login" element={<Login/>} />
                        <Route path="/register" element={<Login register />} />
                        <Route path="/forgotpassword" element={<Login forgotPassword/>} />
                        <Route element={<RequireUser />}>
                                <Route path="/dashboard" element={<Dashboard/>} />
                                <Route path="/dashboard/:folder" element={<Dashboard/>} />
                                <Route path="/dashboard/:folder/:subfolder" element={<Dashboard/>} />
                                <Route path="/dashboard/:folder/:subfolder/:filter" element={<Dashboard/>} />
                                <Route path="/chat" element={<Chat/>} />
                                <Route path="/chat/:id" element={<Chat/>} />
                                <Route path="/knowledge-card/new" element={<KnowledgeCard />} />
                                <Route path="/knowledge-card/:id" element={<KnowledgeCard />} />
                                <Route path="/review/knowledge-card/:id" element={<KnowledgeCard />} />
				<Route element={<RequireRole role="access_template" />}>
					<Route path="/donor-templates/new" element={<DonorTemplateRequest />} />
					<Route path="/donor-templates/:id" element={<DonorTemplateDetail />} />
				</Route>
				<Route element={<RequireRole role="access_quality_gate" />}>
					<Route path="/quality-gate" element={<QualityGate />} />
				</Route>
                        </Route>
                        <Route element={<RequireAdmin />}>
                                <Route path="/admin/access/:resourceType/:resourceId" element={<AccessManagement />} />
                        </Route>
                  </Routes>
                </Suspense>
                {!loading && user && (
                  <Suspense fallback={null}>
                    <WizardModal />
                    <WizardDebug />
                  </Suspense>
                )}
            </>
        )
}

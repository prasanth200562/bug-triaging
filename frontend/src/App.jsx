import { useEffect, useMemo, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import BugReport from './pages/BugReport';
import BugHistory from './pages/BugHistory';
import Developers from './pages/Developers';
import RetrainModel from './pages/RetrainModel';
import Login from './pages/Login';
import UserPortal from './pages/UserPortal';
import DeveloperWorkspace from './pages/DeveloperWorkspace';
import { clearSession, getSession, setSession } from './services/auth';
import './App.css';

const ProtectedRoute = ({ session, allowedRoles }) => {
    if (!session?.token) {
        return <Navigate to="/login" replace />;
    }
    if (!allowedRoles.includes(session.role)) {
        return <Navigate to="/" replace />;
    }
    return <Outlet />;
};

const PortalLayout = ({ role, session, onLogout }) => (
    <div className="dashboard-layout">
        <Sidebar role={role} displayName={session?.full_name || session?.username} onLogout={onLogout} />
        <main className="main-content">
            <Outlet />
        </main>
    </div>
);

const RootRedirect = ({ session }) => {
    const target = useMemo(() => {
        if (session?.role === 'admin') return '/admin';
        if (session?.role === 'developer') return '/developer';
        return '/user/report';
    }, [session]);

    return <Navigate to={target} replace />;
};

const ScrollTop = () => {
    const location = useLocation();
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [location.pathname]);
    return null;
};

function App() {
    const [session, setSessionState] = useState(getSession());

    useEffect(() => {
        if (session?.token) {
            axios.defaults.headers.common.Authorization = `Bearer ${session.token}`;
        } else {
            delete axios.defaults.headers.common.Authorization;
        }
    }, [session]);

    const handleLogin = (authSession) => {
        setSession(authSession);
        setSessionState(authSession);
    };

    const handleLogout = () => {
        clearSession();
        setSessionState(null);
    };

    return (
        <Router>
            <ScrollTop />
            <Routes>
                <Route path="/" element={<RootRedirect session={session} />} />
                <Route path="/login" element={<Login onLogin={handleLogin} />} />

                <Route path="/user/report" element={<UserPortal />} />

                <Route element={<ProtectedRoute session={session} allowedRoles={['developer']} />}>
                    <Route element={<PortalLayout role="developer" session={session} onLogout={handleLogout} />}>
                        <Route path="/developer" element={<DeveloperWorkspace />} />
                        <Route path="/developer/report" element={<BugReport />} />
                    </Route>
                </Route>

                <Route element={<ProtectedRoute session={session} allowedRoles={['admin']} />}>
                    <Route element={<PortalLayout role="admin" session={session} onLogout={handleLogout} />}>
                        <Route path="/admin" element={<Dashboard />} />
                        <Route path="/admin/report" element={<BugReport />} />
                        <Route path="/admin/history" element={<BugHistory />} />
                        <Route path="/admin/developers" element={<Developers />} />
                        <Route path="/admin/retrain" element={<RetrainModel />} />
                    </Route>
                </Route>

                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Router>
    );
}

export default App;

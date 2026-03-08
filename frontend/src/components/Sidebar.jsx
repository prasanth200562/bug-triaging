import { NavLink } from 'react-router-dom';
import { LayoutDashboard, History, FileText, Users, RefreshCw, Zap, ShieldCheck } from 'lucide-react';

const Sidebar = () => {
    return (
        <div className="sidebar">
            <div className="logo-container">
                <div className="logo-icon">
                    <Zap size={24} fill="currentColor" />
                </div>
                <div className="logo-text">BugTriage</div>
            </div>

            <nav className="nav-links" style={{ flex: 1 }}>
                <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <LayoutDashboard size={20} />
                    <span>Analytics</span>
                </NavLink>
                <NavLink to="/report" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <FileText size={20} />
                    <span>Report Issue</span>
                </NavLink>
                <NavLink to="/history" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <History size={20} />
                    <span>Bug Log</span>
                </NavLink>
                <NavLink to="/developers" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <Users size={20} />
                    <span>Team</span>
                </NavLink>
                <NavLink to="/retrain" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                    <RefreshCw size={20} />
                    <span>ML Engine</span>
                </NavLink>
            </nav>

            <div style={{
                marginTop: 'auto',
                padding: '1rem',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <ShieldCheck size={16} className="text-success" />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>System Secure</span>
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    AI Model v1.2.4 Active
                </div>
            </div>
        </div>
    );
};

export default Sidebar;


import { NavLink } from 'react-router-dom';
import { LayoutDashboard, History, FileText, Users, RefreshCw, Zap, ShieldCheck, ClipboardList, LogOut } from 'lucide-react';

const Sidebar = ({ role = 'admin', onLogout, displayName }) => {
    const adminLinks = [
        { to: '/admin', label: 'Analytics', icon: LayoutDashboard },
        { to: '/admin/report', label: 'Report Issue', icon: FileText },
        { to: '/admin/history', label: 'Bug Log', icon: History },
        { to: '/admin/developers', label: 'Team', icon: Users },
        { to: '/admin/retrain', label: 'ML Engine', icon: RefreshCw }
    ];

    const developerLinks = [
        { to: '/developer', label: 'My Queue', icon: ClipboardList },
        { to: '/developer/report', label: 'Quick Report', icon: FileText }
    ];

    const links = role === 'developer' ? developerLinks : adminLinks;

    return (
        <div className="sidebar">
            <div className="logo-container">
                <div className="logo-icon">
                    <Zap size={24} fill="currentColor" />
                </div>
                <div>
                    <div className="logo-text">BugTriage</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        {role} portal
                    </div>
                </div>
            </div>

            <nav className="nav-links" style={{ flex: 1 }}>
                {links.map((link) => {
                    const Icon = link.icon;
                    return (
                        <NavLink key={link.to} to={link.to} end={link.to === '/admin' || link.to === '/developer'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                            <Icon size={20} />
                            <span>{link.label}</span>
                        </NavLink>
                    );
                })}
            </nav>

            <div style={{ marginBottom: '1rem', padding: '0 0.25rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                {displayName || 'Session Active'}
            </div>

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

            {onLogout && (
                <button className="btn btn-secondary" style={{ marginTop: '1rem', width: '100%' }} onClick={onLogout}>
                    <LogOut size={16} /> Logout
                </button>
            )}
        </div>
    );
};

export default Sidebar;


import { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, Mail, Shield, Activity, Award, Globe } from 'lucide-react';

const Developers = () => {
    const [developers, setDevelopers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDevelopers = async () => {
            try {
                const response = await axios.get('/api/users?role=developer');
                setDevelopers(response.data);
            } catch (err) {
                console.error("Error fetching developers:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDevelopers();
    }, []);

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <header style={{ marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.25rem', fontWeight: 700 }}>Engineering Team</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Resource management and active developer synchronization.</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '3rem' }}>
                <div className="card" style={{ padding: '1.5rem', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(255,255,255,0.02))' }}>
                    <div className="flex-between mb-4">
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Talent</span>
                        <Users size={18} className="text-primary" />
                    </div>
                    <div style={{ fontSize: '2rem', fontWeight: 700 }}>{developers.length}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Engineers Assigned</div>
                </div>

                <div className="card" style={{ padding: '1.5rem' }}>
                    <div className="flex-between mb-4">
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Capacity</span>
                        <Activity size={18} className="text-success" />
                    </div>
                    <div style={{ fontSize: '2rem', fontWeight: 700 }}>94%</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>System-wide Bandwidth</div>
                </div>

                <div className="card" style={{ padding: '1.5rem' }}>
                    <div className="flex-between mb-4">
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expertise</span>
                        <Award size={18} className="text-warning" />
                    </div>
                    <div style={{ fontSize: '2rem', fontWeight: 700 }}>12</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Sub-systems Tracked</div>
                </div>

                <div className="card" style={{ padding: '1.5rem' }}>
                    <div className="flex-between mb-4">
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Global Sync</span>
                        <Globe size={18} className="text-accent" />
                    </div>
                    <div style={{ fontSize: '2rem', fontWeight: 700 }}>Active</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Resource Propagation</div>
                </div>
            </div>

            <div className="card" style={{ padding: '0.5rem' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Shield size={20} className="text-primary" />
                    <h3 style={{ margin: 0 }}>Team Resource Directory</h3>
                </div>

                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Engineer Identity</th>
                                <th>Handle</th>
                                <th>Core Role</th>
                                <th>Sync Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {developers.map((dev, idx) => (
                                <tr key={idx}>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <div style={{
                                                width: '36px', height: '36px', borderRadius: '12px',
                                                background: 'linear-gradient(45deg, var(--primary), var(--primary-light))',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontWeight: 700, color: 'white', fontSize: '0.875rem'
                                            }}>
                                                {dev.full_name.charAt(0)}
                                            </div>
                                            <div style={{ fontWeight: 600 }}>{dev.full_name}</div>
                                        </div>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>@{dev.username}</td>
                                    <td>
                                        <span className="tag" style={{ border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.03)' }}>
                                            {dev.role.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)' }}>
                                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'currentColor', boxShadow: '0 0 8px currentColor' }} />
                                            <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em' }}>ONLINE</span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {developers.length === 0 && !loading && (
                                <tr>
                                    <td colSpan="4" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                                        <Users size={32} style={{ opacity: 0.1, marginBottom: '1rem' }} />
                                        <p>No active resources found in the directory.</p>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Developers;


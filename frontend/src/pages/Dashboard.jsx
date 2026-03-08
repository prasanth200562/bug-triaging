import { useState, useEffect } from 'react';
import axios from 'axios';
import StatsCard from '../components/StatsCard';
import { Bug, CheckCircle, AlertTriangle, Clock, Zap, Target, Activity, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        total_bugs: 0,
        auto_assigned: 0,
        manual_review: 0,
        bugs_per_developer: {},
        pending_bugs: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await axios.get('/api/stats');
                setStats(response.data);
            } catch (err) {
                console.error("Error fetching stats:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    const today = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <header style={{ marginBottom: '2.5rem' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{today}</div>
                <h1 style={{ fontSize: '2.25rem', fontWeight: 700 }}>Pulse Analytics</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Strategic overview of system triage performance and developer allocation.</p>
            </header>

            <div className="stats-grid">
                <StatsCard
                    label="System Ingested"
                    value={stats.total_bugs}
                    icon={Bug}
                    color="#6366f1"
                    onClick={() => navigate('/history')}
                />
                <StatsCard
                    label="Auto Assigned"
                    value={stats.auto_assigned}
                    icon={CheckCircle}
                    color="#10b981"
                    onClick={() => navigate('/history?status=assigned')}
                />
                <StatsCard
                    label="Manual Review"
                    value={stats.manual_review}
                    icon={AlertTriangle}
                    color="#f59e0b"
                    onClick={() => navigate('/history?status=manual-review')}
                />
                <StatsCard
                    label="Pending Sync"
                    value={stats.pending_bugs}
                    icon={Clock}
                    color="#3b82f6"
                    onClick={() => navigate('/history?status=open')}
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                <section className="card">
                    <div className="flex-between mb-8">
                        <div>
                            <h2 style={{ margin: 0 }}>Allocation Matrix</h2>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Workload distribution across active developers.</p>
                        </div>
                        <Users size={20} className="text-muted" />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {Object.entries(stats.bugs_per_developer).map(([dev, count], index) => {
                            const percentage = stats.total_bugs > 0 ? (count / stats.total_bugs) * 100 : 0;
                            return (
                                <div key={index}>
                                    <div className="flex-between mb-2">
                                        <span style={{ fontWeight: 600 }}>{dev}</span>
                                        <span className="tag">{count} Tasks</span>
                                    </div>
                                    <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                                        <div
                                            style={{
                                                width: `${percentage}%`,
                                                height: '100%',
                                                background: `linear-gradient(90deg, var(--primary), var(--primary-light))`,
                                                borderRadius: '4px',
                                                transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)'
                                            }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                        {Object.keys(stats.bugs_per_developer).length === 0 && !loading && (
                            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                                <Zap size={32} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                                <p>No active assignments found.</p>
                            </div>
                        )}
                        {loading && <div style={{ color: 'var(--text-muted)' }}>Calculating matrix...</div>}
                    </div>
                </section>

                <section className="card">
                    <div className="flex-between mb-8">
                        <h2 style={{ margin: 0 }}>Real-time Feed</h2>
                        <Activity size={20} className="text-muted" />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {[
                            { title: 'New Bug Sync', time: '2m ago', type: 'info' },
                            { title: 'AI Model Retrained', time: '1h ago', type: 'success' },
                            { title: 'Manual Override', time: '3h ago', type: 'warning' },
                            { title: 'Dev List Updated', time: '1d ago', type: 'info' }
                        ].map((activity, i) => (
                            <div key={i} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                                <div style={{
                                    width: '8px',
                                    height: '8px',
                                    borderRadius: '50%',
                                    background: `var(--${activity.type})`,
                                    marginTop: '6px',
                                    boxShadow: `0 0 8px var(--${activity.type})`
                                }} />
                                <div>
                                    <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{activity.title}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{activity.time}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <button
                        className="btn btn-secondary"
                        style={{ width: '100%', marginTop: '2rem', fontSize: '0.875rem' }}
                        onClick={() => navigate('/history')}
                    >
                        View Full Logs
                    </button>
                </section>
            </div>
        </div>
    );
};

export default Dashboard;


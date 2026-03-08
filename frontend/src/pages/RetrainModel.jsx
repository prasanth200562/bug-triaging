import { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw, Database, Clock, Zap, AlertCircle, CheckCircle, List, Cpu, Activity, TrendingUp } from 'lucide-react';

const RetrainModel = () => {
    const [status, setStatus] = useState(null);
    const [queue, setQueue] = useState([]);
    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState(null);

    const fetchData = async () => {
        try {
            const [statusRes, queueRes] = await Promise.all([
                axios.get('/api/retrain/status'),
                axios.get('/api/retrain/queue')
            ]);
            setStatus(statusRes.data);
            setQueue(queueRes.data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch retraining details');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleTrigger = async () => {
        if (!window.confirm('Initiating neural recalibration. This process executes in the background. Proceed?')) {
            return;
        }

        setTriggering(true);
        setMessage(null);
        try {
            const response = await axios.post('/api/retrain/trigger');
            setMessage(response.data.message);
            setTimeout(fetchData, 2000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to trigger retraining');
        } finally {
            setTriggering(false);
        }
    };

    if (loading && !status) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '1rem' }}>
                <RefreshCw size={40} className="spin text-primary" />
                <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Initializing ML Control Room...</span>
            </div>
        );
    }

    const nextRetrainPercent = status ? Math.min(100, (status.pending_count / status.threshold_cases) * 100) : 0;

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '3rem' }}>
                <div>
                    <h1 style={{ fontSize: '2.25rem', fontWeight: 700 }}>ML Operations</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Neural engine telemetry and manual recalibration controls.</p>
                </div>
                <button
                    onClick={handleTrigger}
                    className="btn btn-primary"
                    disabled={triggering}
                    style={{ position: 'relative', overflow: 'hidden' }}
                >
                    <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', position: 'relative', zIndex: 1 }}>
                        <Cpu size={18} className={triggering ? 'spin' : ''} />
                        {triggering ? 'Recalibrating...' : 'Recalibrate Engine'}
                    </div>
                    {triggering && (
                        <div style={{
                            position: 'absolute', inset: 0,
                            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
                            animation: 'shimmer 1.5s infinite'
                        }} />
                    )}
                </button>
            </header>

            {error && (
                <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(239,68,68,0.1)', borderRadius: 'var(--radius-md)', border: '1px solid var(--danger)', display: 'flex', gap: '0.75rem', alignItems: 'center', color: 'var(--danger)' }}>
                    <AlertCircle size={20} />
                    <span style={{ fontSize: '0.875rem' }}>{error}</span>
                </div>
            )}

            {message && (
                <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(16,185,129,0.1)', borderRadius: 'var(--radius-md)', border: '1px solid var(--success)', display: 'flex', gap: '0.75rem', alignItems: 'center', color: 'var(--success)' }}>
                    <CheckCircle size={20} />
                    <span style={{ fontSize: '0.875rem' }}>{message}</span>
                </div>
            )}

            {/* Neural Telemetry Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '3rem' }}>
                <div className="card" style={{ padding: '1.5rem', position: 'relative' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Queue Saturation</span>
                        <Activity size={18} className="text-primary" />
                    </div>
                    <div style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>{status?.pending_count} / {status?.threshold_cases}</div>
                    <div className="progress-bar mb-4" style={{ height: '4px' }}>
                        <div className="progress-fill" style={{ width: `${nextRetrainPercent}%` }} />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auto-sync at 100% cap</div>
                </div>

                <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Engine State</span>
                        <Zap size={18} className="text-accent" />
                    </div>
                    <div style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>v{status?.model_version}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 8px var(--success)' }} />
                        <span style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: 600 }}>Operational</span>
                    </div>
                </div>

                <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last Sync</span>
                        <Clock size={18} className="text-secondary" />
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                        {status?.last_retrain_date ? new Date(status.last_retrain_date).toLocaleDateString() : 'Initial State'}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>T-interval: {status?.threshold_days} days</span>
                </div>

                <div className="card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Cumulative Intel</span>
                        <TrendingUp size={18} className="text-success" />
                    </div>
                    <div style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>{status?.retrained_count}</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total classified training samples</span>
                </div>
            </div>

            {/* Verification Queue Section */}
            <div className="card" style={{ padding: '0.5rem' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Database size={20} className="text-primary" />
                    <h3 style={{ margin: 0 }}>Pending Recalibration Samples</h3>
                </div>

                <div className="table-container">
                    {queue.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                            <Activity size={32} style={{ opacity: 0.1, marginBottom: '1rem' }} />
                            <p>Neural buffer is currently clear.</p>
                            <p style={{ fontSize: '0.875rem' }}>As new classified samples arrive, they will appear here for verification.</p>
                        </div>
                    ) : (
                        <table style={{ margin: 0 }}>
                            <thead>
                                <tr>
                                    <th>Incident Ref</th>
                                    <th>Title</th>
                                    <th>Verified Agent</th>
                                    <th>Ingestion Date</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {queue.map((item) => (
                                    <tr key={item.id}>
                                        <td style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>#{item.bug_id}</td>
                                        <td style={{ maxWidth: '400px' }}>
                                            <div style={{ fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.title}</div>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem' }}>
                                                    {item.verified_developer.charAt(0)}
                                                </div>
                                                <span style={{ fontSize: '0.875rem' }}>{item.verified_developer}</span>
                                            </div>
                                        </td>
                                        <td style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                                            {new Date(item.added_at).toLocaleString()}
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--warning)' }} />
                                                <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--warning)', letterSpacing: '0.05em' }}>Staged</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
                .spin {
                    animation: rotate 1.5s linear infinite;
                }
                @keyframes rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}} />
        </div>
    );
};

export default RetrainModel;


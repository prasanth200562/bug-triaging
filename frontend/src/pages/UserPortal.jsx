import { useMemo, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Send, Github, FileJson, Search, UserRound, CheckCircle2, Clock3 } from 'lucide-react';

const StatusBadge = ({ status }) => {
    const cls = status === 'resolved' ? 'status-assigned' : 'status-open';
    return <span className={`status-badge ${cls}`}>{status}</span>;
};

const UserPortal = () => {
    const [reporter, setReporter] = useState('');
    const [formData, setFormData] = useState({ title: '', body: '', priority: 'medium', source: 'manual' });
    const [loading, setLoading] = useState(false);
    const [importing, setImporting] = useState(false);
    const [importKind, setImportKind] = useState(null);
    const [githubCount, setGithubCount] = useState(5);
    const [localCount, setLocalCount] = useState(5);
    const [result, setResult] = useState(null);
    const [myBugs, setMyBugs] = useState([]);
    const [error, setError] = useState('');

    const canSubmit = useMemo(() => reporter.trim().length > 1, [reporter]);

    const submitManual = async (event) => {
        event.preventDefault();
        if (!canSubmit) {
            setError('Please enter your name to track your bug reports.');
            return;
        }

        setLoading(true);
        setError('');
        try {
            const payload = { ...formData, reporter_username: reporter };
            const response = await axios.post('/api/predict', payload);
            setResult(response.data);
            await fetchMyBugs();
            setFormData({ title: '', body: '', priority: 'medium', source: 'manual' });
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to submit report');
        } finally {
            setLoading(false);
        }
    };

    const importMethod = async (kind) => {
        if (!canSubmit) {
            setError('Enter reporter name first so imported bugs can be tracked.');
            return;
        }

        setImporting(true);
        setImportKind(kind);
        setError('');
        try {
            if (kind === 'github') {
                await axios.post('/api/fetch-github', { count: Number(githubCount) || 5, reporter_username: reporter });
            } else {
                await axios.post('/api/import-local', { count: Number(localCount) || 5, reporter_username: reporter });
            }
            await fetchMyBugs();
        } catch (err) {
            setError(err.response?.data?.detail || 'Import failed');
        } finally {
            setImporting(false);
            setImportKind(null);
        }
    };

    const fetchMyBugs = async () => {
        if (!canSubmit) {
            return;
        }
        const response = await axios.get('/api/user/bugs', { params: { reporter } });
        setMyBugs(response.data);
    };

    return (
        <div style={{ animation: 'fadeIn 0.4s ease-out' }}>
            <div className="public-topbar">
                <div>
                    <h1 style={{ marginBottom: '0.35rem' }}>User Bug Portal</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Report from 3 channels and track assignee + progress in real-time.</p>
                </div>
                <Link className="btn btn-secondary" to="/login">Admin / Developer Login</Link>
            </div>

            <div className="public-grid">
                <div className="card">
                    <h2 style={{ marginBottom: '1rem' }}>Report A Bug</h2>
                    <div className="form-group mb-4">
                        <label>Your Name</label>
                        <div style={{ position: 'relative' }}>
                            <UserRound size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                            <input className="form-input" style={{ paddingLeft: '2.2rem' }} value={reporter} onChange={(e) => setReporter(e.target.value)} placeholder="e.g. Prasanth" />
                        </div>
                    </div>

                    <form onSubmit={submitManual}>
                        <div className="form-group mb-4">
                            <label>Title</label>
                            <input className="form-input" value={formData.title} onChange={(e) => setFormData((p) => ({ ...p, title: e.target.value }))} required />
                        </div>
                        <div className="form-group mb-4">
                            <label>Priority</label>
                            <select className="form-input" value={formData.priority} onChange={(e) => setFormData((p) => ({ ...p, priority: e.target.value }))}>
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        <div className="form-group mb-8">
                            <label>Description</label>
                            <textarea className="form-input" rows={6} value={formData.body} onChange={(e) => setFormData((p) => ({ ...p, body: e.target.value }))} required />
                        </div>
                        <button className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                            <Send size={16} /> {loading ? 'Submitting...' : 'Submit Manually'}
                        </button>
                    </form>

                    {result && (
                        <div style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
                            Routed to <strong style={{ color: 'var(--text-primary)' }}>{result.predictions?.[0]?.predicted_developer || 'Pending review'}</strong>
                        </div>
                    )}

                    {error && <div style={{ color: 'var(--danger)', marginTop: '1rem' }}>{error}</div>}
                </div>

                <div style={{ display: 'grid', gap: '1rem' }}>
                    <div className="card">
                        <h3 style={{ marginBottom: '0.8rem' }}>Method 2: GitHub Fetch</h3>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Import open issues in bulk.</p>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <input className="form-input" type="number" value={githubCount} onChange={(e) => setGithubCount(e.target.value)} />
                            <button className="btn btn-secondary" onClick={() => importMethod('github')} disabled={importing}>
                                <Github size={16} /> {importing && importKind === 'github' ? 'Fetching...' : 'Fetch'}
                            </button>
                        </div>
                    </div>

                    <div className="card">
                        <h3 style={{ marginBottom: '0.8rem' }}>Method 3: Local Import</h3>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Load historical bugs from local dataset.</p>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <input className="form-input" type="number" value={localCount} onChange={(e) => setLocalCount(e.target.value)} />
                            <button className="btn btn-secondary" onClick={() => importMethod('local')} disabled={importing}>
                                <FileJson size={16} /> {importing && importKind === 'local' ? 'Importing...' : 'Import'}
                            </button>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex-between mb-4">
                            <h3 style={{ margin: 0 }}>My Reported Bugs</h3>
                            <button className="btn btn-secondary" onClick={fetchMyBugs} disabled={!canSubmit}><Search size={16} /> Refresh</button>
                        </div>
                        <div style={{ display: 'grid', gap: '0.6rem' }}>
                            {myBugs.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No bugs yet for this reporter.</p>}
                            {myBugs.map((bug) => (
                                <div key={bug.id} style={{ padding: '0.75rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
                                    <div className="flex-between mb-2">
                                        <strong>#{bug.id} {bug.title}</strong>
                                        <StatusBadge status={bug.workflow_status} />
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', gap: '1rem' }}>
                                        <span style={{ display: 'inline-flex', gap: '0.3rem', alignItems: 'center' }}><UserRound size={14} /> {bug.assigned_to || 'Not assigned yet'}</span>
                                        <span style={{ display: 'inline-flex', gap: '0.3rem', alignItems: 'center' }}>{bug.workflow_status === 'resolved' ? <CheckCircle2 size={14} /> : <Clock3 size={14} />} {bug.workflow_status}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserPortal;

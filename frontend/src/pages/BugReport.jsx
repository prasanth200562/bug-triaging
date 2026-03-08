import { useState } from 'react';
import axios from 'axios';
import { Send, CheckCircle, AlertCircle, Github, FileJson, Info, Zap, ChevronRight, Target } from 'lucide-react';

const BugReport = () => {
    const [formData, setFormData] = useState({ title: '', body: '', priority: 'medium', source: 'manual' });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [githubCount, setGithubCount] = useState(5);
    const [githubLoading, setGithubLoading] = useState(false);
    const [githubResult, setGithubResult] = useState(null);
    const [localCount, setLocalCount] = useState(5);
    const [localLoading, setLocalLoading] = useState(false);

    const handleGithubFetch = async () => {
        setGithubLoading(true);
        setError(null);
        setGithubResult(null);

        try {
            const response = await axios.post('/api/fetch-github', { count: githubCount });
            setGithubResult(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to fetch from GitHub');
        } finally {
            setGithubLoading(false);
        }
    };

    const handleLocalImport = async () => {
        setLocalLoading(true);
        setError(null);
        setGithubResult(null);

        try {
            const response = await axios.post('/api/import-local', { count: localCount });
            setGithubResult(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to import from local file');
        } finally {
            setLocalLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        setGithubResult(null);

        try {
            const response = await axios.post('/api/predict', formData);
            setResult(response.data);
            setFormData({ title: '', body: '', priority: 'medium', source: 'manual' });
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (Array.isArray(detail)) {
                setError(detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(', '));
            } else {
                setError(detail || err.message || 'An error occurred');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <header style={{ marginBottom: '2.5rem' }}>
                <h1 style={{ fontSize: '2.25rem', fontWeight: 700 }}>Intake & Triage</h1>
                <p style={{ color: 'var(--text-secondary)' }}>Log issues manually or sync from external repositories for AI-driven classification.</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '2.5rem', alignItems: 'start' }}>
                {/* Manual Form Section */}
                <section>
                    <div className="card">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
                            <Zap size={20} className="text-primary" fill="currentColor" />
                            <h2 style={{ margin: 0 }}>Manual Incident Report</h2>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group mb-4">
                                <label>Short Title</label>
                                <input
                                    className="form-input"
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    placeholder="e.g. Memory leak in LSP server"
                                    required
                                />
                            </div>

                            <div className="form-group mb-4">
                                <label>Severity Level</label>
                                <select
                                    className="form-input"
                                    value={formData.priority}
                                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                                >
                                    <option value="low">Low - Minor UX adjustments</option>
                                    <option value="medium">Medium - Normal operational issues</option>
                                    <option value="high">High - Impacting core features</option>
                                    <option value="critical">Critical - System crash or data loss</option>
                                </select>
                            </div>

                            <div className="form-group mb-8">
                                <label>Technical Context</label>
                                <textarea
                                    className="form-input"
                                    value={formData.body}
                                    onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                                    placeholder="Explain the technical details, error logs, and steps to reproduce..."
                                    rows={8}
                                    required
                                />
                            </div>

                            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                                {loading ? 'Neural Processing...' : <><Send size={18} /> Run AI Triage Engine</>}
                            </button>
                        </form>

                        {error && (
                            <div style={{ marginTop: '1.5rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', padding: '1rem', borderRadius: 'var(--radius-md)', color: 'var(--danger)', display: 'flex', gap: '0.75rem' }}>
                                <AlertCircle size={20} /> <span style={{ fontSize: '0.875rem' }}>{error}</span>
                            </div>
                        )}
                    </div>

                    {result && (
                        <div className="card" style={{ marginTop: '2rem', borderLeft: '4px solid var(--primary)' }}>
                            <div className="flex-between mb-8">
                                <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <Target size={18} className="text-primary" />
                                    Triage Classification
                                </h3>
                                <span className={`status-badge status-${result.issue_status === 'NEW_DEVELOPER_CASE' ? 'review' : (result.is_auto_assigned ? 'assigned' : 'review')}`}>
                                    {result.issue_status === 'NEW_DEVELOPER_CASE' ? 'New Developer Detected' : (result.is_auto_assigned ? 'Auto-Assigned' : 'Review Required')}
                                </span>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                {result.predictions.map((pred, idx) => (
                                    <div key={idx} style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                                        <span style={{ fontWeight: 600 }}>{pred.predicted_developer}</span>
                                    </div>
                                ))}
                            </div>

                            {result.is_auto_assigned ? (
                                <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16, 185, 129, 0.2)', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                    <CheckCircle size={18} className="text-success" />
                                    <span style={{ fontSize: '0.875rem' }}>Automated route confirmed for <strong>{result.predictions[0].predicted_developer}</strong>.</span>
                                </div>
                            ) : (
                                <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(99, 102, 241, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(99, 102, 241, 0.2)', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                    <Info size={18} className="text-primary" />
                                    <span style={{ fontSize: '0.875rem' }}>Confidence below threshold. Manual verification is requested.</span>
                                </div>
                            )}
                        </div>
                    )}
                </section>

                {/* Bulk Import Section */}
                <aside style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                    <div className="card">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                            <Github size={20} className="text-secondary" />
                            <h3 style={{ margin: 0 }}>Repository Sync</h3>
                        </div>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Pull direct data from connected GitHub repositories for mass processing.</p>

                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                            <input
                                className="form-input"
                                type="number"
                                value={githubCount}
                                onChange={(e) => setGithubCount(e.target.value)}
                                style={{ width: '80px' }}
                            />
                            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleGithubFetch} disabled={githubLoading}>
                                {githubLoading ? 'Syncing...' : 'Sync Repository'}
                            </button>
                        </div>
                    </div>

                    <div className="card">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                            <FileJson size={20} className="text-accent" />
                            <h3 style={{ margin: 0 }}>Local Seed</h3>
                        </div>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Import historical bug data from pre-processed local datasets.</p>

                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                            <input
                                className="form-input"
                                type="number"
                                value={localCount}
                                onChange={(e) => setLocalCount(e.target.value)}
                                style={{ width: '80px' }}
                            />
                            <button className="btn btn-secondary" style={{ flex: 1 }} onClick={handleLocalImport} disabled={localLoading}>
                                {localLoading ? 'Importing...' : 'Seed Data'}
                            </button>
                        </div>
                    </div>

                    {githubResult && (
                        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                            <div className="card" style={{ background: 'rgba(255,255,255,0.03)' }}>
                                <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem' }}>Import Summary</h3>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--success)' }}>{githubResult.imported_count}</div>
                                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Success</div>
                                    </div>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--warning)' }}>{githubResult.skipped_count}</div>
                                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Duplicate</div>
                                    </div>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--danger)' }}>{githubResult.error_count}</div>
                                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Failed</div>
                                    </div>
                                </div>

                                {githubResult.imported_count > 0 && (
                                    <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                        {githubResult.imported.slice(0, 3).map((bug, i) => (
                                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                <ChevronRight size={14} className="text-primary" />
                                                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{bug.title}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </aside>
            </div>
        </div>
    );
};

export default BugReport;


import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import { Search, Filter, ExternalLink, User as UserIcon, Trash2, ChevronRight, X, ShieldAlert, CheckCircle2 } from 'lucide-react';

const BugHistory = () => {
    const { search } = useLocation();
    const query = new URLSearchParams(search);
    const filterStatus = query.get('status');

    const [bugs, setBugs] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState([]);

    // Assignment Modal State
    const [selectedBug, setSelectedBug] = useState(null);
    const [allDevelopers, setAllDevelopers] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [targetDev, setTargetDev] = useState({ id: null, name: '' });
    const [assignmentLoading, setAssignmentLoading] = useState(false);

    useEffect(() => {
        fetchBugs();
        fetchDevelopers();
    }, []);

    const fetchBugs = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/bugs');
            setBugs(response.data);
        } catch (err) {
            console.error("Error fetching bugs:", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchDevelopers = async () => {
        try {
            const response = await axios.get('/api/users?role=developer');
            setAllDevelopers(response.data);
        } catch (err) {
            console.error("Error fetching developers:", err);
        }
    };

    const handleOpenAssign = async (bug) => {
        setSelectedBug(bug);
        setAssignmentLoading(true);
        try {
            const resp = await axios.get(`/api/bugs/${bug.id}/predictions`);
            const preds = resp.data.predictions;
            setSuggestions(preds);

            if (preds.length > 0) {
                const top = preds[0];
                const dev = allDevelopers.find(d => d.full_name === top.predicted_developer);
                setTargetDev({ id: dev?.id || null, name: top.predicted_developer });
            }
        } catch (err) {
            console.error("Error fetching predictions:", err);
            setSuggestions([]);
        } finally {
            setAssignmentLoading(false);
        }
    };

    const handleAssign = async () => {
        if (!targetDev.name) return;
        try {
            await axios.post(`/api/bugs/${selectedBug.id}/assign`, {
                developer_id: targetDev.id,
                developer_name: targetDev.name
            });
            setSelectedBug(null);
            fetchBugs();
        } catch (err) {
            alert("Failed to assign: " + err.message);
        }
    };

    const handleDelete = async (bugId) => {
        if (!window.confirm(`Are you sure you want to delete bug #${bugId}?`)) return;
        try {
            await axios.delete(`/api/bugs/${bugId}`);
            fetchBugs();
        } catch (err) {
            alert("Failed to delete bug: " + err.message);
        }
    };

    const handleBulkDelete = async () => {
        if (!window.confirm(`Are you sure you want to delete ${selectedIds.length} selected bugs?`)) return;
        try {
            await axios.post('/api/bugs/bulk-delete', { bug_ids: selectedIds });
            setSelectedIds([]);
            fetchBugs();
        } catch (err) {
            alert("Failed to delete bugs: " + err.message);
        }
    };

    const toggleSelectAll = () => {
        if (selectedIds.length === filteredBugs.length) {
            setSelectedIds([]);
        } else {
            setSelectedIds(filteredBugs.map(b => b.id));
        }
    };

    const toggleSelect = (id) => {
        setSelectedIds(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const filteredBugs = bugs.filter(bug => {
        const matchesSearch = bug.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            bug.id.toString().includes(searchTerm);
        const matchesStatus = filterStatus ? bug.status === filterStatus : true;
        return matchesSearch && matchesStatus;
    });

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            {/* Modal Overlay */}
            {selectedBug && (
                <div style={{
                    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
                    backdropFilter: 'blur(8px)', zIndex: 1000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem'
                }}>
                    <div className="card" style={{
                        maxWidth: '550px', width: '100%',
                        border: '1px solid var(--border)',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                    }}>
                        <div className="flex-between mb-8">
                            <h2 style={{ margin: 0 }}>Strategic Assignment</h2>
                            <button onClick={() => setSelectedBug(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                                <X size={20} />
                            </button>
                        </div>

                        <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Active Incident #{selectedBug.id}</div>
                            <div style={{ fontWeight: 600 }}>{selectedBug.title}</div>
                        </div>

                        {assignmentLoading ? (
                            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                <ActivityLoader />
                                <div style={{ marginTop: '1rem' }}>Consulting AI Engine...</div>
                            </div>
                        ) : (
                            <>
                                <div style={{ marginBottom: '2rem' }}>
                                    <div style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <ShieldAlert size={16} className="text-primary" />
                                        Confidence-Stacked Suggestions
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                        {suggestions.map((p, i) => (
                                            <button
                                                key={i}
                                                onClick={() => {
                                                    const dev = allDevelopers.find(d => d.full_name === p.predicted_developer);
                                                    setTargetDev({ id: dev?.id || null, name: p.predicted_developer });
                                                }}
                                                style={{
                                                    width: '100%',
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center',
                                                    padding: '1rem',
                                                    background: targetDev.name === p.predicted_developer ? 'rgba(99, 102, 241, 0.1)' : 'rgba(255,255,255,0.02)',
                                                    border: `1px solid ${targetDev.name === p.predicted_developer ? 'var(--primary)' : 'var(--border)'}`,
                                                    borderRadius: 'var(--radius-md)',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease'
                                                }}
                                            >
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                    <UserIcon size={16} className="text-muted" />
                                                    <span style={{ fontWeight: 500, color: 'white' }}>{p.predicted_developer}</span>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group mb-8">
                                    <label>Manual Override</label>
                                    <select
                                        className="form-input"
                                        value={targetDev.name}
                                        onChange={(e) => {
                                            const dev = allDevelopers.find(d => d.full_name === e.target.value);
                                            setTargetDev({ id: dev?.id || null, name: e.target.value });
                                        }}
                                    >
                                        <option value="">Select from team...</option>
                                        {allDevelopers.map((dev, i) => (
                                            <option key={i} value={dev.full_name}>{dev.full_name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div style={{ display: 'flex', gap: '1rem' }}>
                                    <button className="btn btn-primary" onClick={handleAssign} disabled={!targetDev.name} style={{ flex: 1 }}>Confirm Route</button>
                                    <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setSelectedBug(null)}>Decline</button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2.5rem' }}>
                <header>
                    <h1 style={{ fontSize: '2.25rem', fontWeight: 700 }}>Bug Registry</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Comprehensive audit log of all system incidents and triage operations.
                        {filterStatus && <span style={{ color: 'var(--primary)', marginLeft: '0.5rem' }}>• Filtered by {filterStatus}</span>}
                    </p>
                </header>
                {filterStatus && (
                    <button className="btn btn-secondary" onClick={() => window.location.href = '/history'} style={{ fontSize: '0.75rem' }}>
                        Clear Filters
                    </button>
                )}
            </div>

            <div className="card" style={{ padding: '0.5rem' }}>
                <div style={{ padding: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <div style={{ position: 'relative', flex: 1 }}>
                        <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="form-input"
                            type="text"
                            placeholder="Quantum search registry by title, ID, or component..."
                            style={{ paddingLeft: '3rem', background: 'rgba(255,255,255,0.02)' }}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    {selectedIds.length > 0 && (
                        <button
                            className="btn btn-danger"
                            onClick={handleBulkDelete}
                            style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}
                        >
                            <Trash2 size={18} /> Purge ({selectedIds.length})
                        </button>
                    )}
                </div>

                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style={{ width: '40px' }}>
                                    <input
                                        type="checkbox"
                                        checked={filteredBugs.length > 0 && selectedIds.length === filteredBugs.length}
                                        onChange={toggleSelectAll}
                                    />
                                </th>
                                <th>Incident</th>
                                <th>Classification</th>
                                <th>Strategic Assignee</th>
                                <th>Operations</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredBugs.map(bug => {
                                const latestAssignment = bug.assignments?.[bug.assignments.length - 1];
                                return (
                                    <tr key={bug.id} className={selectedIds.includes(bug.id) ? 'selected-row' : ''}>
                                        <td>
                                            <input
                                                type="checkbox"
                                                checked={selectedIds.includes(bug.id)}
                                                onChange={() => toggleSelect(bug.id)}
                                            />
                                        </td>
                                        <td style={{ maxWidth: '400px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: 700 }}>#{bug.id}</div>
                                                <div style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{bug.title}</div>
                                            </div>
                                            <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.5rem' }}>
                                                {bug.tags?.split(',').map((tag, i) => (
                                                    <span key={i} className={`tag ${tag.trim() === 'New Developer' ? 'tag-new-dev' : ''}`}>
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`status-badge status-${bug.status}`}>
                                                {bug.status === 'new-developer' ? 'New Developer Detected' : bug.status.replace('-', ' ')}
                                            </span>
                                        </td>

                                        <td>
                                            {latestAssignment ? (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', color: 'white' }}>
                                                        {latestAssignment.developer_name.charAt(0)}
                                                    </div>
                                                    <div>
                                                        <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{latestAssignment.developer_name}</div>
                                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{latestAssignment.assignment_type}</div>
                                                    </div>
                                                </div>
                                            ) : <span className="text-muted">Unrouted</span>}
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '0.25rem' }}>
                                                <button className="icon-btn" onClick={() => handleOpenAssign(bug)} title="Strategic Route">
                                                    <ChevronRight size={18} />
                                                </button>
                                                <button className="icon-btn text-danger" onClick={() => handleDelete(bug.id)} title="Purge Record">
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const ActivityLoader = () => (
    <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
        {[0, 1, 2].map(i => (
            <div key={i} style={{
                width: '8px', height: '8px', background: 'var(--primary)', borderRadius: '50%',
                animation: `pulse 1s ease-in-out infinite ${i * 0.2}s`
            }} />
        ))}
    </div>
);

export default BugHistory;


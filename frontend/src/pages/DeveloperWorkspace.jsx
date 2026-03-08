import { useEffect, useState } from 'react';
import axios from 'axios';
import { CheckCircle2, Clock3 } from 'lucide-react';

const DeveloperWorkspace = () => {
    const [bugs, setBugs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busyId, setBusyId] = useState(null);

    const fetchBugs = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/developer/bugs');
            setBugs(response.data);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBugs();
    }, []);

    const updateStatus = async (bugId, status) => {
        setBusyId(bugId);
        try {
            const response = await axios.patch(`/api/developer/bugs/${bugId}/status`, { status });
            setBugs((prev) => prev.map((bug) => (bug.id === bugId ? response.data : bug)));
        } finally {
            setBusyId(null);
        }
    };

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <header style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '2.2rem' }}>Developer Queue</h1>
                <p style={{ color: 'var(--text-secondary)' }}>See assigned bugs and mark each bug as pending or resolved.</p>
            </header>

            <div className="card">
                {loading && <p style={{ color: 'var(--text-secondary)' }}>Loading assigned bugs...</p>}
                {!loading && bugs.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No bugs assigned right now.</p>}

                <div style={{ display: 'grid', gap: '0.9rem' }}>
                    {bugs.map((bug) => {
                        const resolved = bug.workflow_status === 'resolved';
                        return (
                            <div key={bug.id} style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
                                <div className="flex-between mb-4">
                                    <div>
                                        <div style={{ fontWeight: 700 }}>#{bug.id} {bug.title}</div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Assigned to: {bug.assigned_to || 'N/A'}</div>
                                    </div>
                                    <span className={`status-badge ${resolved ? 'status-assigned' : 'status-open'}`}>{bug.workflow_status}</span>
                                </div>
                                <div style={{ display: 'flex', gap: '0.6rem' }}>
                                    <button className="btn btn-secondary" disabled={busyId === bug.id} onClick={() => updateStatus(bug.id, 'pending')}>
                                        <Clock3 size={16} /> Pending
                                    </button>
                                    <button className="btn btn-primary" disabled={busyId === bug.id} onClick={() => updateStatus(bug.id, 'resolved')}>
                                        <CheckCircle2 size={16} /> Resolved
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default DeveloperWorkspace;

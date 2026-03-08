import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Shield, Wrench, LogIn, AlertCircle } from 'lucide-react';

const Login = ({ onLogin }) => {
    const navigate = useNavigate();
    const [form, setForm] = useState({ username: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await axios.post('/api/auth/login', form);
            onLogin(response.data);
            if (response.data.role === 'admin') {
                navigate('/admin');
            } else {
                navigate('/developer');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-screen">
            <div className="auth-glow auth-glow-left" />
            <div className="auth-glow auth-glow-right" />
            <div className="auth-card">
                <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Control Access</h1>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                    Sign in as Admin or Developer. Users can continue via public reporting.
                </p>

                <form onSubmit={handleSubmit}>
                    <div className="form-group mb-4">
                        <label>Username</label>
                        <input
                            className="form-input"
                            value={form.username}
                            onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
                            placeholder="admin or developer name"
                            required
                        />
                    </div>

                    <div className="form-group mb-8">
                        <label>Password</label>
                        <input
                            className="form-input"
                            type="password"
                            value={form.password}
                            onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                            placeholder="admin123 or dev123"
                            required
                        />
                    </div>

                    <button className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                        <LogIn size={16} /> {loading ? 'Verifying...' : 'Sign In'}
                    </button>
                </form>

                {error && (
                    <div style={{ marginTop: '1rem', color: 'var(--danger)', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <AlertCircle size={16} /> {error}
                    </div>
                )}

                <div className="auth-hints">
                    <div className="auth-hint-card">
                        <Shield size={16} className="text-primary" />
                        <div>
                            <strong>Admin</strong>
                            <p>username `admin` / password `admin123`</p>
                        </div>
                    </div>
                    <div className="auth-hint-card">
                        <Wrench size={16} className="text-success" />
                        <div>
                            <strong>Developer</strong>
                            <p>username your developer name / password `dev123`</p>
                        </div>
                    </div>
                </div>

                <button className="btn btn-secondary" style={{ width: '100%', marginTop: '1rem' }} onClick={() => navigate('/user/report')}>
                    Continue As User Reporter
                </button>
            </div>
        </div>
    );
};

export default Login;

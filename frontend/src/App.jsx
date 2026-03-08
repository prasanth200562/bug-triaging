import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import BugReport from './pages/BugReport';
import BugHistory from './pages/BugHistory';
import Developers from './pages/Developers';
import RetrainModel from './pages/RetrainModel';
import './App.css';

function App() {
    return (
        <Router>
            <div className="dashboard-layout">
                <Sidebar />
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/report" element={<BugReport />} />
                        <Route path="/history" element={<BugHistory />} />
                        <Route path="/developers" element={<Developers />} />
                        <Route path="/retrain" element={<RetrainModel />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;

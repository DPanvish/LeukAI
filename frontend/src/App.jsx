import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { AnimatePresence } from 'framer-motion';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import DiagnosticViewer from './pages/DiagnosticViewer';
import History from './pages/History';
import Layout from './components/Layout';

function ProtectedRoute({ children }) {
    const { isAuthenticated } = useAuth();
    return isAuthenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
    return (
        <>
            {/* Animated background blobs */}
            <div className="bg-blob-blue" style={{ top: '-200px', left: '-200px' }} />
            <div className="bg-blob-purple" style={{ bottom: '-100px', right: '-150px' }} />

            <AnimatePresence mode="wait">
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route
                        path="/"
                        element={
                            <ProtectedRoute>
                                <Layout />
                            </ProtectedRoute>
                        }
                    >
                        <Route index element={<Dashboard />} />
                        <Route path="upload" element={<Upload />} />
                        <Route path="diagnostic/:id" element={<DiagnosticViewer />} />
                        <Route path="history" element={<History />} />
                    </Route>
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AnimatePresence>
        </>
    );
}

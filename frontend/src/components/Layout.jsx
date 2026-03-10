import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import {
    LayoutDashboard,
    Upload,
    History,
    LogOut,
    Activity,
    Menu,
    X,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/upload', icon: Upload, label: 'Upload Scan' },
    { to: '/history', icon: History, label: 'Patient History' },
];

export default function Layout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="flex min-h-screen relative z-10">
            {/* ── Mobile overlay ─────────────────────────────── */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* ── Sidebar ────────────────────────────────────── */}
            <aside
                className={`fixed lg:sticky top-0 left-0 h-screen w-72 glass z-50 flex flex-col transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    }`}
            >
                {/* Logo */}
                <div className="p-6 border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                            <Activity className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="font-display text-xl font-bold gradient-text">LeukAI</h1>
                            <p className="text-xs text-gray-500">Detection Platform</p>
                        </div>
                    </div>
                </div>

                {/* Nav links */}
                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map(({ to, icon: Icon, label, end }) => (
                        <NavLink
                            key={to}
                            to={to}
                            end={end}
                            onClick={() => setSidebarOpen(false)}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${isActive
                                    ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                                }`
                            }
                        >
                            <Icon className="w-5 h-5" />
                            {label}
                        </NavLink>
                    ))}
                </nav>

                {/* User card */}
                <div className="p-4 border-t border-white/5">
                    <div className="glass-light rounded-xl p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-semibold text-gray-200">
                                    {user?.full_name || user?.username || 'Doctor'}
                                </p>
                                <p className="text-xs text-gray-500 capitalize">{user?.role || 'doctor'}</p>
                            </div>
                            <button
                                onClick={handleLogout}
                                className="p-2 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-400 transition-colors"
                                title="Logout"
                            >
                                <LogOut className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </aside>

            {/* ── Main Content ───────────────────────────────── */}
            <main className="flex-1 min-h-screen">
                {/* Mobile header */}
                <div className="lg:hidden sticky top-0 z-30 glass px-4 py-3 flex items-center justify-between">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="p-2 rounded-lg hover:bg-white/5"
                    >
                        <Menu className="w-5 h-5" />
                    </button>
                    <h1 className="font-display text-lg font-bold gradient-text">LeukAI</h1>
                    <div className="w-9" />
                </div>

                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.3 }}
                    className="p-6 lg:p-8"
                >
                    <Outlet />
                </motion.div>
            </main>
        </div>
    );
}

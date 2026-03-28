import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Activity, Lock, User, ArrowRight, Eye, EyeOff, UserPlus } from 'lucide-react';

export default function Signup() {
    const { signup, loading, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [showPass, setShowPass] = useState(false);

    // Redirect if already logged in
    if (isAuthenticated) {
        navigate('/', { replace: true });
        return null;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        const ok = await signup(username, password, fullName);
        if (ok) navigate('/', { replace: true });
    };

    return (
        <div className="min-h-screen flex relative z-10">
            {/* ── Left: Hero ────────────────────────────────── */}
            <div className="hidden lg:flex flex-1 items-center justify-center p-12 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-950 via-surface-900 to-accent-950" />
                <div className="absolute top-20 left-20 w-72 h-72 rounded-full bg-primary-500/10 blur-3xl" />
                <div className="absolute bottom-20 right-20 w-96 h-96 rounded-full bg-accent-500/8 blur-3xl" />

                <motion.div
                    initial={{ opacity: 0, x: -40 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8 }}
                    className="relative z-10 max-w-lg"
                >
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-glow">
                            <Activity className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h1 className="font-display text-3xl font-bold gradient-text">LeukAI</h1>
                            <p className="text-sm text-gray-400">Detection Platform</p>
                        </div>
                    </div>

                    <h2 className="text-4xl font-display font-bold text-white leading-tight mb-6">
                        AI-Powered Leukemia
                        <br />
                        <span className="gradient-text">Second Opinion</span>
                    </h2>

                    <p className="text-gray-400 text-lg leading-relaxed mb-8">
                        Join our platform to upload Peripheral Blood Smear images for instant AI-driven classification
                        with Grad-CAM heatmap visualization highlighting regions of interest.
                    </p>

                    <div className="flex gap-6">
                        {[
                            { num: '99.2%', label: 'Accuracy' },
                            { num: '< 3s', label: 'Analysis' },
                            { num: '4', label: 'Classes' },
                        ].map(({ num, label }) => (
                            <div key={label} className="text-center">
                                <p className="text-2xl font-display font-bold text-white">{num}</p>
                                <p className="text-xs text-gray-500">{label}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>

            {/* ── Right: Signup Form ─────────────────────────── */}
            <div className="flex-1 flex items-center justify-center p-8">
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="w-full max-w-md"
                >
                    {/* Mobile logo */}
                    <div className="lg:hidden flex items-center gap-3 mb-10 justify-center">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                            <Activity className="w-6 h-6 text-white" />
                        </div>
                        <h1 className="font-display text-2xl font-bold gradient-text">LeukAI</h1>
                    </div>

                    <div className="glass-card p-8 gradient-border">
                        <div className="mb-8">
                            <h2 className="text-2xl font-display font-bold text-white mb-2">Create an account</h2>
                            <p className="text-gray-400">Sign up to access the diagnostic platform</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            {/* Full Name */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                                <div className="relative">
                                    <UserPlus className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <input
                                        id="signup-fullname"
                                        type="text"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        className="input-field pl-11"
                                        placeholder="Enter full name"
                                        required
                                        autoFocus
                                    />
                                </div>
                            </div>
                            
                            {/* Username */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                                <div className="relative">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <input
                                        id="signup-username"
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="input-field pl-11"
                                        placeholder="Choose a username"
                                        required
                                    />
                                </div>
                            </div>

                            {/* Password */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <input
                                        id="signup-password"
                                        type={showPass ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="input-field pl-11 pr-11"
                                        placeholder="Create a password"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPass(!showPass)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                                    >
                                        {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>

                            {/* Submit */}
                            <motion.button
                                id="signup-submit"
                                type="submit"
                                disabled={loading}
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.99 }}
                                className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 mt-6"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>
                                        Sign Up
                                        <ArrowRight className="w-4 h-4" />
                                    </>
                                )}
                            </motion.button>
                        </form>

                        <div className="mt-6 text-center">
                            <p className="text-sm text-gray-400">
                                Already have an account?{' '}
                                <Link to="/login" className="text-primary-400 hover:text-primary-300 transition-colors">
                                    Sign in
                                </Link>
                            </p>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}

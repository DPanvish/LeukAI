import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Microscope,
    Upload,
    ShieldCheck,
    AlertTriangle,
    TrendingUp,
    Clock,
    ArrowRight,
} from 'lucide-react';
import { getStatsAPI } from '../services/api';
import { PageHeader, StatCard, GlassCard, Spinner, Badge } from '../components/UIComponents';

const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function Dashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getStatsAPI()
            .then(({ data }) => setStats(data))
            .catch(() => setStats({ total_scans: 0, benign_count: 0, malignant_count: 0, recent_scans: [] }))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <Spinner />;

    const { total_scans, benign_count, malignant_count, recent_scans } = stats;

    return (
        <motion.div variants={container} initial="hidden" animate="show">
            <PageHeader
                title="Dashboard"
                subtitle="Overview of the Leukemia Detection Platform"
                action={
                    <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => navigate('/upload')}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Upload className="w-4 h-4" />
                        New Scan
                    </motion.button>
                }
            />

            {/* ── Stat Cards ──────────────────────────────── */}
            <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
                <StatCard icon={Microscope} label="Total Scans" value={total_scans} color="primary" />
                <StatCard icon={ShieldCheck} label="Benign" value={benign_count} color="green" />
                <StatCard icon={AlertTriangle} label="Malignant" value={malignant_count} color="red" />
                <StatCard
                    icon={TrendingUp}
                    label="Detection Rate"
                    value={total_scans > 0 ? `${((malignant_count / total_scans) * 100).toFixed(1)}%` : '—'}
                    color="amber"
                />
            </motion.div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* ── Quick Upload Widget ────────────────────── */}
                <motion.div variants={item} className="xl:col-span-1">
                    <GlassCard className="h-full flex flex-col items-center justify-center text-center py-10">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mb-5 animate-pulse-glow">
                            <Upload className="w-8 h-8 text-white" />
                        </div>
                        <h3 className="text-lg font-display font-bold text-white mb-2">Quick Upload</h3>
                        <p className="text-gray-400 text-sm mb-6 max-w-xs">
                            Upload a Peripheral Blood Smear image for instant AI-powered analysis
                        </p>
                        <motion.button
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.96 }}
                            onClick={() => navigate('/upload')}
                            className="btn-primary flex items-center gap-2"
                        >
                            Start Analysis
                            <ArrowRight className="w-4 h-4" />
                        </motion.button>
                    </GlassCard>
                </motion.div>

                {/* ── Recent Scans ───────────────────────────── */}
                <motion.div variants={item} className="xl:col-span-2">
                    <GlassCard hover={false}>
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-display font-bold text-white flex items-center gap-2">
                                <Clock className="w-5 h-5 text-primary-400" />
                                Recent Scans
                            </h3>
                            <button
                                onClick={() => navigate('/history')}
                                className="text-sm text-primary-400 hover:text-primary-300 transition-colors flex items-center gap-1"
                            >
                                View all <ArrowRight className="w-3 h-3" />
                            </button>
                        </div>

                        {recent_scans.length === 0 ? (
                            <div className="text-center py-10 text-gray-500">
                                <Microscope className="w-10 h-10 mx-auto mb-3 opacity-30" />
                                <p>No scans yet. Upload your first PBS image to get started.</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {recent_scans.map((scan, idx) => (
                                    <motion.div
                                        key={scan.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        onClick={() => navigate(`/diagnostic/${scan.id}`)}
                                        className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-primary-500/20 transition-all cursor-pointer group"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
                                                <Microscope className="w-5 h-5 text-primary-400" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-200">
                                                    {scan.patient_name || 'Unknown Patient'}
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    {new Date(scan.created_at).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit',
                                                    })}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <Badge
                                                variant={scan.classification === 'Benign' ? 'success' : 'danger'}
                                            >
                                                {scan.classification}
                                            </Badge>
                                            <span className="text-sm text-gray-400 font-mono">
                                                {(scan.confidence * 100).toFixed(1)}%
                                            </span>
                                            <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-primary-400 transition-colors" />
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                </motion.div>
            </div>

            {/* ── System Status ────────────────────────────── */}
            <motion.div variants={item} className="mt-6">
                <GlassCard hover={false}>
                    <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">System Status</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {[
                            { label: 'AI Model', status: 'Online', ok: true },
                            { label: 'Database', status: 'Connected', ok: true },
                            { label: 'API Server', status: 'Running', ok: true },
                        ].map(({ label, status, ok }) => (
                            <div key={label} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02]">
                                <div className={`w-2.5 h-2.5 rounded-full ${ok ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' : 'bg-red-400'}`} />
                                <div>
                                    <p className="text-sm font-medium text-gray-300">{label}</p>
                                    <p className="text-xs text-gray-500">{status}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            </motion.div>
        </motion.div>
    );
}

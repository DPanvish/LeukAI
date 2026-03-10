import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search,
    Microscope,
    ArrowRight,
    ChevronLeft,
    ChevronRight,
    Clock,
    Filter,
} from 'lucide-react';
import { getHistoryAPI } from '../services/api';
import { PageHeader, GlassCard, Spinner, Badge, EmptyState } from '../components/UIComponents';

const PAGE_SIZE = 10;

export default function History() {
    const navigate = useNavigate();
    const [records, setRecords] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(0);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [searchInput, setSearchInput] = useState('');

    const fetchHistory = useCallback(async () => {
        setLoading(true);
        try {
            const { data } = await getHistoryAPI(page * PAGE_SIZE, PAGE_SIZE, search);
            setRecords(data.records);
            setTotal(data.total);
        } catch {
            setRecords([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    }, [page, search]);

    useEffect(() => {
        fetchHistory();
    }, [fetchHistory]);

    const handleSearch = (e) => {
        e.preventDefault();
        setPage(0);
        setSearch(searchInput);
    };

    const totalPages = Math.ceil(total / PAGE_SIZE);

    return (
        <div>
            <PageHeader
                title="Patient History"
                subtitle={`${total} diagnostic record${total !== 1 ? 's' : ''} found`}
            />

            {/* ── Search Bar ──────────────────────────── */}
            <GlassCard hover={false} className="mb-6 !p-4">
                <form onSubmit={handleSearch} className="flex gap-3">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <input
                            id="history-search"
                            type="text"
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            className="input-field pl-11 !py-2.5"
                            placeholder="Search by patient name, ID, or classification..."
                        />
                    </div>
                    <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        type="submit"
                        className="btn-primary !py-2.5 flex items-center gap-2"
                    >
                        <Filter className="w-4 h-4" />
                        Search
                    </motion.button>
                </form>
            </GlassCard>

            {/* ── Table ────────────────────────────────── */}
            {loading ? (
                <Spinner />
            ) : records.length === 0 ? (
                <EmptyState
                    icon={Microscope}
                    title="No records found"
                    description={
                        search
                            ? `No results for "${search}". Try a different search term.`
                            : 'Upload your first PBS image to start building patient history.'
                    }
                    action={
                        !search && (
                            <motion.button
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                                onClick={() => navigate('/upload')}
                                className="btn-primary"
                            >
                                Upload First Scan
                            </motion.button>
                        )
                    }
                />
            ) : (
                <GlassCard hover={false} className="overflow-hidden !p-0">
                    {/* Desktop table */}
                    <div className="hidden md:block overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/5">
                                    {['Patient', 'Patient ID', 'Classification', 'Confidence', 'Date', ''].map(
                                        (h) => (
                                            <th
                                                key={h}
                                                className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider"
                                            >
                                                {h}
                                            </th>
                                        )
                                    )}
                                </tr>
                            </thead>
                            <tbody>
                                <AnimatePresence>
                                    {records.map((r, idx) => (
                                        <motion.tr
                                            key={r._id}
                                            initial={{ opacity: 0, y: 8 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0 }}
                                            transition={{ delay: idx * 0.03 }}
                                            onClick={() => navigate(`/diagnostic/${r._id}`)}
                                            className="border-b border-white/[0.03] hover:bg-white/[0.03] cursor-pointer transition-colors group"
                                        >
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center flex-shrink-0">
                                                        <Microscope className="w-4 h-4 text-primary-400" />
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-200">
                                                        {r.patient_name || 'Unknown'}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-400 font-mono">
                                                {r.patient_id || '—'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <Badge variant={r.classification === 'Benign' ? 'success' : 'danger'}>
                                                    {r.classification}
                                                </Badge>
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-300 font-mono">
                                                {(r.confidence * 100).toFixed(1)}%
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-1.5 text-sm text-gray-400">
                                                    <Clock className="w-3.5 h-3.5" />
                                                    {new Date(r.created_at).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric',
                                                    })}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-primary-400 transition-colors" />
                                            </td>
                                        </motion.tr>
                                    ))}
                                </AnimatePresence>
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile cards */}
                    <div className="md:hidden p-4 space-y-3">
                        {records.map((r, idx) => (
                            <motion.div
                                key={r._id}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.03 }}
                                onClick={() => navigate(`/diagnostic/${r._id}`)}
                                className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-primary-500/20 transition-all cursor-pointer"
                            >
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-sm font-medium text-gray-200">
                                        {r.patient_name || 'Unknown'}
                                    </span>
                                    <Badge variant={r.classification === 'Benign' ? 'success' : 'danger'}>
                                        {r.classification}
                                    </Badge>
                                </div>
                                <div className="flex items-center justify-between text-xs text-gray-400">
                                    <span>{r.patient_id || '—'}</span>
                                    <span className="font-mono">{(r.confidence * 100).toFixed(1)}%</span>
                                    <span>
                                        {new Date(r.created_at).toLocaleDateString('en-US', {
                                            month: 'short',
                                            day: 'numeric',
                                        })}
                                    </span>
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* ── Pagination ────────────────────────── */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between px-6 py-4 border-t border-white/5">
                            <p className="text-sm text-gray-500">
                                Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
                            </p>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                                    disabled={page === 0}
                                    className="p-2 rounded-lg hover:bg-white/5 disabled:opacity-30 text-gray-400"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                                    const p = page < 3 ? i : page - 2 + i;
                                    if (p >= totalPages) return null;
                                    return (
                                        <button
                                            key={p}
                                            onClick={() => setPage(p)}
                                            className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${p === page
                                                    ? 'bg-primary-500/15 text-primary-400 border border-primary-500/20'
                                                    : 'text-gray-400 hover:bg-white/5'
                                                }`}
                                        >
                                            {p + 1}
                                        </button>
                                    );
                                })}
                                <button
                                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                                    disabled={page >= totalPages - 1}
                                    className="p-2 rounded-lg hover:bg-white/5 disabled:opacity-30 text-gray-400"
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </GlassCard>
            )}
        </div>
    );
}

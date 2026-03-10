import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    ArrowLeft,
    Download,
    Microscope,
    Flame,
    BarChart3,
    Calendar,
    User,
    Hash,
    StickyNote,
    FileText,
} from 'lucide-react';
import { getRecordAPI } from '../services/api';
import { GlassCard, PageHeader, Spinner, Badge } from '../components/UIComponents';
import jsPDF from 'jspdf';
import toast from 'react-hot-toast';

export default function DiagnosticViewer() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [record, setRecord] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('sideBySide');

    useEffect(() => {
        getRecordAPI(id)
            .then(({ data }) => setRecord(data))
            .catch(() => {
                toast.error('Failed to load record');
                navigate('/history');
            })
            .finally(() => setLoading(false));
    }, [id]);

    const generatePDF = async () => {
        if (!record) return;

        try {
            const pdf = new jsPDF('p', 'mm', 'a4');
            const w = pdf.internal.pageSize.getWidth();
            const ph = pdf.internal.pageSize.getHeight();

            // ── Header ───────────────────────────────────
            pdf.setFillColor(10, 14, 26);
            pdf.rect(0, 0, w, 45, 'F');
            pdf.setTextColor(255, 255, 255);
            pdf.setFontSize(22);
            pdf.setFont('helvetica', 'bold');
            pdf.text('LeukAI - Diagnostic Report', 15, 20);
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            pdf.setTextColor(180, 180, 190);
            pdf.text('Generated: ' + new Date().toLocaleString(), 15, 30);
            pdf.text('Record ID: ' + (record._id || 'N/A'), 15, 37);

            // ── Patient Info ─────────────────────────────
            let y = 55;
            pdf.setTextColor(40, 40, 50);
            pdf.setFontSize(14);
            pdf.setFont('helvetica', 'bold');
            pdf.text('Patient Information', 15, y);
            y += 10;
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            pdf.text('Name: ' + (record.patient_name || 'N/A'), 15, y);
            pdf.text('ID: ' + (record.patient_id || 'N/A'), 110, y);
            y += 7;
            pdf.text('Date: ' + new Date(record.created_at).toLocaleString(), 15, y);
            y += 7;
            if (record.notes) {
                pdf.text('Notes: ' + record.notes, 15, y);
                y += 7;
            }

            // ── Classification ───────────────────────────
            y += 8;
            pdf.setFontSize(14);
            pdf.setFont('helvetica', 'bold');
            pdf.text('Classification Result', 15, y);
            y += 10;
            pdf.setFontSize(12);
            const isBenign = record.classification === 'Benign';
            pdf.setTextColor(isBenign ? 34 : 239, isBenign ? 197 : 68, isBenign ? 94 : 68);
            pdf.text(
                record.classification + '  -  ' + (record.confidence * 100).toFixed(2) + '% confidence',
                15, y
            );
            y += 10;

            // ── Probabilities ────────────────────────────
            pdf.setTextColor(40, 40, 50);
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            if (record.all_probabilities) {
                Object.entries(record.all_probabilities).forEach(([cls, prob]) => {
                    const barWidth = Math.max(prob * 120, 1);
                    // Draw probability bar background
                    pdf.setFillColor(230, 230, 235);
                    pdf.rect(60, y - 3, 120, 5, 'F');
                    // Draw probability bar fill
                    if (cls === record.classification) {
                        pdf.setFillColor(isBenign ? 34 : 239, isBenign ? 197 : 68, isBenign ? 94 : 68);
                    } else {
                        pdf.setFillColor(100, 100, 120);
                    }
                    pdf.rect(60, y - 3, barWidth, 5, 'F');
                    // Text
                    pdf.setTextColor(40, 40, 50);
                    pdf.text(cls + ':', 20, y);
                    pdf.text((prob * 100).toFixed(2) + '%', 183, y, { align: 'right' });
                    y += 8;
                });
            }

            // ── Images ───────────────────────────────────
            y += 5;
            pdf.setFontSize(14);
            pdf.setFont('helvetica', 'bold');
            pdf.setTextColor(40, 40, 50);
            pdf.text('Diagnostic Images', 15, y);
            y += 8;

            const imgSize = 75;

            if (record.image_base64) {
                pdf.setFontSize(9);
                pdf.setFont('helvetica', 'normal');
                pdf.text('Original PBS Image', 15, y);
                y += 3;
                try {
                    pdf.addImage(
                        'data:image/png;base64,' + record.image_base64,
                        'PNG', 15, y, imgSize, imgSize
                    );
                } catch (imgErr) {
                    pdf.setTextColor(150, 150, 150);
                    pdf.text('[Image could not be embedded]', 15, y + 20);
                }
            }
            if (record.heatmap_base64) {
                pdf.setFontSize(9);
                pdf.text('Grad-CAM Heatmap', 105, y - 3);
                try {
                    pdf.addImage(
                        'data:image/png;base64,' + record.heatmap_base64,
                        'PNG', 105, y, imgSize, imgSize
                    );
                } catch (imgErr) {
                    pdf.setTextColor(150, 150, 150);
                    pdf.text('[Heatmap could not be embedded]', 105, y + 20);
                }
            }

            // ── Footer ───────────────────────────────────
            pdf.setFontSize(8);
            pdf.setTextColor(150, 150, 160);
            pdf.text(
                'Disclaimer: This AI-generated report is for second-opinion purposes only. Always confirm with clinical findings.',
                15,
                ph - 10
            );
            pdf.setTextColor(180, 180, 190);
            pdf.text('LeukAI Detection Platform', w - 15, ph - 10, { align: 'right' });

            pdf.save('LeukAI_Report_' + (record._id || 'unknown') + '.pdf');
            toast.success('PDF report downloaded');
        } catch (err) {
            console.error('PDF generation failed:', err);
            toast.error('PDF export failed: ' + err.message);
        }
    };

    if (loading) return <Spinner />;
    if (!record) return null;

    const isBenign = record.classification === 'Benign';

    return (
        <div>
            <PageHeader
                title="Diagnostic Viewer"
                subtitle={`Record: ${record._id}`}
                action={
                    <div className="flex gap-3">
                        <motion.button
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.97 }}
                            onClick={() => navigate(-1)}
                            className="btn-secondary flex items-center gap-2"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back
                        </motion.button>
                        <motion.button
                            id="download-pdf-btn"
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.97 }}
                            onClick={generatePDF}
                            className="btn-primary flex items-center gap-2"
                        >
                            <Download className="w-4 h-4" />
                            Export PDF
                        </motion.button>
                    </div>
                }
            />

            {/* ── Classification Result Banner ────────── */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`mb-6 p-5 rounded-2xl border ${isBenign
                    ? 'bg-emerald-500/5 border-emerald-500/20'
                    : 'bg-red-500/5 border-red-500/20'
                    }`}
            >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div
                            className={`p-3 rounded-xl ${isBenign ? 'bg-emerald-500/10' : 'bg-red-500/10'
                                }`}
                        >
                            <Microscope className={`w-6 h-6 ${isBenign ? 'text-emerald-400' : 'text-red-400'}`} />
                        </div>
                        <div>
                            <p className="text-sm text-gray-400">Classification</p>
                            <p className={`text-2xl font-display font-bold ${isBenign ? 'text-emerald-400' : 'text-red-400'}`}>
                                {record.classification}
                            </p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-gray-400">Confidence</p>
                        <p className="text-3xl font-display font-bold text-white">
                            {(record.confidence * 100).toFixed(1)}%
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* ── Tab Navigation ──────────────────────── */}
            <div className="flex gap-2 mb-6">
                {[
                    { key: 'sideBySide', label: 'Side by Side' },
                    { key: 'original', label: 'Original' },
                    { key: 'heatmap', label: 'Heatmap' },
                ].map(({ key, label }) => (
                    <button
                        key={key}
                        onClick={() => setActiveTab(key)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeTab === key
                            ? 'bg-primary-500/15 text-primary-400 border border-primary-500/20'
                            : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
                            }`}
                    >
                        {label}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* ── Image Comparison ──────────────────── */}
                <div className="xl:col-span-2">
                    <GlassCard hover={false}>
                        {activeTab === 'sideBySide' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Microscope className="w-4 h-4 text-primary-400" />
                                        <p className="text-sm font-medium text-gray-300">Original Image</p>
                                    </div>
                                    <div className="rounded-xl overflow-hidden bg-black/30 border border-white/5 flex items-center justify-center aspect-square">
                                        <img
                                            src={`data:image/png;base64,${record.image_base64}`}
                                            alt="Original PBS"
                                            className="w-full h-full object-contain"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Flame className="w-4 h-4 text-accent-400" />
                                        <p className="text-sm font-medium text-gray-300">Grad-CAM Heatmap</p>
                                    </div>
                                    <div className="rounded-xl overflow-hidden bg-black/30 border border-white/5 flex items-center justify-center aspect-square">
                                        <img
                                            src={`data:image/png;base64,${record.heatmap_base64}`}
                                            alt="Grad-CAM Heatmap"
                                            className="w-full h-full object-contain"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}
                        {activeTab === 'original' && (
                            <div className="flex items-center justify-center">
                                <img
                                    src={`data:image/png;base64,${record.image_base64}`}
                                    alt="Original PBS"
                                    className="max-w-full max-h-[500px] object-contain rounded-xl"
                                />
                            </div>
                        )}
                        {activeTab === 'heatmap' && (
                            <div className="flex items-center justify-center">
                                <img
                                    src={`data:image/png;base64,${record.heatmap_base64}`}
                                    alt="Grad-CAM Heatmap"
                                    className="max-w-full max-h-[500px] object-contain rounded-xl"
                                />
                            </div>
                        )}
                    </GlassCard>
                </div>

                {/* ── Details Panel ─────────────────────── */}
                <div className="space-y-4">
                    {/* Probabilities */}
                    <GlassCard hover={false}>
                        <div className="flex items-center gap-2 mb-4">
                            <BarChart3 className="w-4 h-4 text-primary-400" />
                            <h3 className="text-sm font-semibold text-gray-300">Class Probabilities</h3>
                        </div>
                        <div className="space-y-3">
                            {record.all_probabilities &&
                                Object.entries(record.all_probabilities)
                                    .sort(([, a], [, b]) => b - a)
                                    .map(([cls, prob]) => (
                                        <div key={cls}>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-300">{cls}</span>
                                                <span className="text-gray-400 font-mono">{(prob * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="w-full h-2 rounded-full bg-white/5 overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${prob * 100}%` }}
                                                    transition={{ duration: 0.8, ease: 'easeOut' }}
                                                    className={`h-full rounded-full ${cls === record.classification
                                                        ? isBenign
                                                            ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                                                            : 'bg-gradient-to-r from-red-500 to-red-400'
                                                        : 'bg-gradient-to-r from-gray-600 to-gray-500'
                                                        }`}
                                                />
                                            </div>
                                        </div>
                                    ))}
                        </div>
                    </GlassCard>

                    {/* Patient Info */}
                    <GlassCard hover={false}>
                        <h3 className="text-sm font-semibold text-gray-300 mb-4">Record Details</h3>
                        <div className="space-y-3 text-sm">
                            {[
                                { icon: User, label: 'Patient', value: record.patient_name || 'N/A' },
                                { icon: Hash, label: 'Patient ID', value: record.patient_id || 'N/A' },
                                { icon: FileText, label: 'File', value: record.image_filename },
                                {
                                    icon: Calendar,
                                    label: 'Date',
                                    value: new Date(record.created_at).toLocaleString(),
                                },
                            ].map(({ icon: Icon, label, value }) => (
                                <div key={label} className="flex items-start gap-3">
                                    <Icon className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                                    <div>
                                        <p className="text-gray-500">{label}</p>
                                        <p className="text-gray-300 break-all">{value}</p>
                                    </div>
                                </div>
                            ))}
                            {record.notes && (
                                <div className="flex items-start gap-3">
                                    <StickyNote className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                                    <div>
                                        <p className="text-gray-500">Notes</p>
                                        <p className="text-gray-300">{record.notes}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
}

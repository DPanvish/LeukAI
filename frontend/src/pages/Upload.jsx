import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload as UploadIcon,
    Image,
    X,
    FileCheck,
    AlertCircle,
    Loader2,
    User,
    Hash,
    StickyNote,
} from 'lucide-react';
import { uploadImageAPI } from '../services/api';
import { PageHeader, GlassCard } from '../components/UIComponents';
import toast from 'react-hot-toast';

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const ACCEPTED = { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'], 'image/bmp': ['.bmp'], 'image/tiff': ['.tiff'] };

export default function Upload() {
    const navigate = useNavigate();
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [patientName, setPatientName] = useState('');
    const [patientId, setPatientId] = useState('');
    const [notes, setNotes] = useState('');
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    const onDrop = useCallback((accepted, rejected) => {
        setError('');
        if (rejected.length > 0) {
            const err = rejected[0].errors[0];
            setError(
                err.code === 'file-too-large'
                    ? 'File too large. Maximum 10 MB.'
                    : 'Invalid file type. Use JPG, PNG, BMP, or TIFF.'
            );
            return;
        }
        if (accepted.length > 0) {
            const f = accepted[0];
            setFile(f);
            setPreview(URL.createObjectURL(f));
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: ACCEPTED,
        maxSize: MAX_SIZE,
        multiple: false,
    });

    const clearFile = () => {
        setFile(null);
        setPreview(null);
        setError('');
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('patient_name', patientName);
        formData.append('patient_id', patientId);
        formData.append('notes', notes);

        try {
            const { data } = await uploadImageAPI(formData);
            toast.success(`Analysis complete: ${data.classification} (${(data.confidence * 100).toFixed(1)}%)`);
            navigate(`/diagnostic/${data.id}`);
        } catch (err) {
            const msg = err.response?.data?.detail || 'Upload failed. Please try again.';
            setError(msg);
            toast.error(msg);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div>
            <PageHeader
                title="Upload PBS Image"
                subtitle="Drag and drop a Peripheral Blood Smear image for AI analysis"
            />

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* ── Dropzone ──────────────────────────────── */}
                <div className="lg:col-span-3">
                    <GlassCard hover={false} className="min-h-[420px] flex flex-col">
                        <AnimatePresence mode="wait">
                            {!file ? (
                                <motion.div
                                    key="dropzone"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    {...getRootProps()}
                                    className={`flex-1 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300 ${isDragActive
                                            ? 'border-primary-400 bg-primary-500/5'
                                            : 'border-white/10 hover:border-primary-500/30 hover:bg-white/[0.02]'
                                        }`}
                                >
                                    <input {...getInputProps()} id="file-dropzone" />
                                    <motion.div
                                        animate={isDragActive ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
                                        className="p-5 rounded-2xl bg-gradient-to-br from-primary-500/15 to-accent-500/15 mb-6"
                                    >
                                        <UploadIcon className="w-10 h-10 text-primary-400" />
                                    </motion.div>
                                    <p className="text-lg font-display font-semibold text-white mb-2">
                                        {isDragActive ? 'Drop it here!' : 'Drag & drop your image'}
                                    </p>
                                    <p className="text-sm text-gray-400 mb-4">or click to browse files</p>
                                    <div className="flex gap-2 flex-wrap justify-center">
                                        {['JPG', 'PNG', 'BMP', 'TIFF'].map((ext) => (
                                            <span
                                                key={ext}
                                                className="px-2 py-1 text-xs rounded-md bg-white/5 text-gray-400 border border-white/5"
                                            >
                                                .{ext.toLowerCase()}
                                            </span>
                                        ))}
                                        <span className="px-2 py-1 text-xs rounded-md bg-white/5 text-gray-400 border border-white/5">
                                            Max 10 MB
                                        </span>
                                    </div>
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="preview"
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    className="flex-1 flex flex-col"
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <FileCheck className="w-5 h-5 text-emerald-400" />
                                            <div>
                                                <p className="text-sm font-medium text-gray-200">{file.name}</p>
                                                <p className="text-xs text-gray-500">
                                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={clearFile}
                                            className="p-2 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-400 transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                    <div className="flex-1 flex items-center justify-center rounded-xl overflow-hidden bg-black/20 border border-white/5">
                                        <img
                                            src={preview}
                                            alt="Preview"
                                            className="max-w-full max-h-[320px] object-contain rounded-lg"
                                        />
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Error */}
                        <AnimatePresence>
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 10 }}
                                    className="mt-4 flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                                >
                                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                    {error}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </GlassCard>
                </div>

                {/* ── Patient Info + Submit ──────────────────── */}
                <div className="lg:col-span-2 space-y-6">
                    <GlassCard hover={false}>
                        <h3 className="text-lg font-display font-bold text-white mb-5">Patient Details</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    <User className="w-3.5 h-3.5 inline mr-1" /> Patient Name
                                </label>
                                <input
                                    id="patient-name"
                                    type="text"
                                    value={patientName}
                                    onChange={(e) => setPatientName(e.target.value)}
                                    className="input-field"
                                    placeholder="e.g. John Doe"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    <Hash className="w-3.5 h-3.5 inline mr-1" /> Patient ID
                                </label>
                                <input
                                    id="patient-id"
                                    type="text"
                                    value={patientId}
                                    onChange={(e) => setPatientId(e.target.value)}
                                    className="input-field"
                                    placeholder="e.g. PT-00123"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    <StickyNote className="w-3.5 h-3.5 inline mr-1" /> Notes
                                </label>
                                <textarea
                                    id="patient-notes"
                                    rows={3}
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    className="input-field resize-none"
                                    placeholder="Additional clinical notes..."
                                />
                            </div>
                        </div>
                    </GlassCard>

                    <motion.button
                        id="run-analysis-btn"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        disabled={!file || uploading}
                        onClick={handleUpload}
                        className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-lg disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {uploading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <Image className="w-5 h-5" />
                                Run AI Analysis
                            </>
                        )}
                    </motion.button>

                    <GlassCard hover={false} className="!p-4">
                        <p className="text-xs text-gray-500 text-center">
                            ⚕️ This tool provides a <strong className="text-gray-400">second opinion</strong> only.
                            Always correlate with clinical findings and consult a haematologist for diagnosis.
                        </p>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
}

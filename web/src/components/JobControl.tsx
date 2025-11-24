'use client';

import { useState } from 'react';
import { Play, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function JobControl() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error' | null, msg: string }>({ type: null, msg: '' });

    const startJob = async () => {
        setLoading(true);
        setStatus({ type: null, msg: 'Initializing pipeline...' });

        try {
            const res = await fetch('/api/process', {
                method: 'POST',
            });
            const data = await res.json();

            if (res.ok) {
                setStatus({ type: 'success', msg: `Job started: ${data.message}` });
            } else {
                setStatus({ type: 'error', msg: `Error: ${data.error}` });
            }
        } catch (e) {
            setStatus({ type: 'error', msg: 'Failed to connect to server' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel p-6 rounded-xl">
            <div className="flex flex-col gap-6">
                <div className="space-y-2">
                    <label className="text-sm text-gray-400 uppercase tracking-wider font-semibold">Configuration</label>
                    <select className="w-full bg-black/20 border border-white/10 rounded-md p-2 text-sm text-gray-200 focus:outline-none focus:border-cyan-500 transition-colors">
                        <option>Demo Configuration (Default)</option>
                        <option>High Resolution (Sentinel-2)</option>
                        <option>SAR Analysis (Sentinel-1)</option>
                    </select>
                </div>

                <button
                    onClick={startJob}
                    disabled={loading}
                    className="group relative w-full overflow-hidden rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 p-[1px] focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50"
                >
                    <div className="relative flex items-center justify-center gap-2 rounded-lg bg-slate-900/90 px-4 py-3 transition-all group-hover:bg-slate-900/0">
                        {loading ? (
                            <Loader2 className="animate-spin text-white" size={20} />
                        ) : (
                            <Play className="text-cyan-400 group-hover:text-white transition-colors" size={20} />
                        )}
                        <span className="font-semibold text-white">Start Processing Job</span>
                    </div>
                </button>

                <AnimatePresence mode="wait">
                    {status.msg && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className={`p-3 rounded-lg text-sm flex items-center gap-2 ${status.type === 'error'
                                    ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                    : 'bg-green-500/10 text-green-400 border border-green-500/20'
                                }`}
                        >
                            {status.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
                            {status.msg}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

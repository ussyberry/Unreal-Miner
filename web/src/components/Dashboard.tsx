'use client';

import { motion } from 'framer-motion';
import JobControl from './JobControl';
import MapViewer from './MapViewer';
import { Activity, Layers, Database, Cpu } from 'lucide-react';

const container = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
};

export default function Dashboard() {
    return (
        <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 lg:grid-cols-12 gap-8"
        >
            {/* Left Column - Controls & Stats */}
            <div className="lg:col-span-4 space-y-8">
                <motion.section variants={item}>
                    <h2 className="text-xl font-bold mb-4 text-cyan-400 flex items-center gap-2">
                        <Cpu size={20} /> Pipeline Control
                    </h2>
                    <JobControl />
                </motion.section>

                <motion.section variants={item} className="glass-panel p-6 rounded-xl">
                    <h2 className="text-xl font-bold mb-4 text-purple-400 flex items-center gap-2">
                        <Activity size={20} /> System Status
                    </h2>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center border-b border-white/10 pb-2">
                            <span className="text-gray-400">Status</span>
                            <span className="text-green-400 font-mono text-sm">ONLINE</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-white/10 pb-2">
                            <span className="text-gray-400">GPU Usage</span>
                            <span className="text-cyan-400 font-mono text-sm">0% (Idle)</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-white/10 pb-2">
                            <span className="text-gray-400">Queue</span>
                            <span className="text-gray-200 font-mono text-sm">Empty</span>
                        </div>
                    </div>
                </motion.section>
            </div>

            {/* Right Column - Visualization */}
            <div className="lg:col-span-8 space-y-8">
                <motion.div variants={item}>
                    <MapViewer />
                </motion.div>

                <motion.section variants={item} className="glass-panel p-6 rounded-xl">
                    <h2 className="text-xl font-bold mb-4 text-cyan-400 flex items-center gap-2">
                        <Layers size={20} /> Asset Gallery
                    </h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="aspect-square bg-white/5 rounded-lg border border-white/10 flex flex-col items-center justify-center text-gray-500 hover:bg-white/10 transition-colors cursor-pointer group">
                                <Database size={24} className="mb-2 group-hover:text-cyan-400 transition-colors" />
                                <span className="text-xs">Asset_{i}</span>
                            </div>
                        ))}
                    </div>
                </motion.section>
            </div>
        </motion.div>
    );
}

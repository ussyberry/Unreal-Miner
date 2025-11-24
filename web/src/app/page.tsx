import Dashboard from '@/components/Dashboard';

export default function Home() {
    return (
        <main className="min-h-screen p-8 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

            <div className="max-w-7xl mx-auto relative z-10">
                <header className="mb-12 text-center">
                    <h1 className="text-5xl font-extrabold tracking-tight mb-4">
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Unreal Miner
                        </span>{" "}
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">
                            Dashboard
                        </span>
                    </h1>
                    <p className="text-lg text-gray-400 max-w-2xl mx-auto">
                        Advanced Satellite Data Processing & Unreal Engine Asset Generation Pipeline
                    </p>
                </header>

                <Dashboard />
            </div>
        </main>
    );
}

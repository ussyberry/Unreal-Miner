'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import MapContainer to avoid SSR issues with Leaflet
const MapContainer = dynamic(
    () => import('react-leaflet').then((mod) => mod.MapContainer),
    { ssr: false }
);
const TileLayer = dynamic(
    () => import('react-leaflet').then((mod) => mod.TileLayer),
    { ssr: false }
);
const Marker = dynamic(
    () => import('react-leaflet').then((mod) => mod.Marker),
    { ssr: false }
);
const Popup = dynamic(
    () => import('react-leaflet').then((mod) => mod.Popup),
    { ssr: false }
);

export default function MapViewer() {
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);
    'use client';

    import { useEffect, useState } from 'react';
    import dynamic from 'next/dynamic';

    // Dynamically import MapContainer to avoid SSR issues with Leaflet
    const MapContainer = dynamic(
        () => import('react-leaflet').then((mod) => mod.MapContainer),
        { ssr: false }
    );
    const TileLayer = dynamic(
        () => import('react-leaflet').then((mod) => mod.TileLayer),
        { ssr: false }
    );
    const Marker = dynamic(
        () => import('react-leaflet').then((mod) => mod.Marker),
        { ssr: false }
    );
    const Popup = dynamic(
        () => import('react-leaflet').then((mod) => mod.Popup),
        { ssr: false }
    );

    export default function MapViewer() {
        const [isMounted, setIsMounted] = useState(false);

        useEffect(() => {
            setIsMounted(true);
        }, []);

        if (!isMounted) {
            return <div className="h-[400px] bg-gray-100 animate-pulse rounded-lg"></div>;
        }

        return (
            <div className="glass-panel p-6 rounded-xl h-full">
                <h2 className="text-xl font-bold mb-4 text-cyan-400 flex items-center gap-2">
                    Satellite Preview
                </h2>
                <div className="h-[400px] rounded-lg overflow-hidden border border-white/10 relative z-0">
                    {/* @ts-ignore - Types for dynamic imports can be tricky */}
                    <MapContainer center={[51.505, -0.09]} zoom={13} style={{ height: '100%', width: '100%' }}>
                        {/* @ts-ignore */}
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        />
                    </MapContainer>
                </div>
                <p className="text-xs text-gray-500 mt-3 font-mono">
                    * Previewing Sentinel-2 basemap (Dark Matter)
                </p>
            </div>
        );
    }

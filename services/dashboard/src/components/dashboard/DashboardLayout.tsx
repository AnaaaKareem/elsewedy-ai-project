'use client';
import React, { useState } from 'react';
import Header from '@/components/Header';
import LeftPanel from './LeftPanel';
import ContextPanel from './ContextPanel';
import Map from './Map';
import BottomPanel from './BottomPanel';

export default function DashboardLayout({ initialData }: { initialData: any[] }) {
    const [selectedCountry, setSelectedCountry] = useState<string | null>("Egypt");

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-primary/30">
            <Header />

            {/* MAIN GRID SYSTEM */}
            <main className="flex-1 grid grid-cols-12 gap-4 p-4 h-[calc(100vh-64px)] overflow-hidden">

                {/* 1. LEFT: MARKET LIST (3 Cols) */}
                <div className="col-span-3 h-full overflow-hidden">
                    <LeftPanel data={initialData} selectedCountry={selectedCountry} />
                </div>

                {/* 2. CENTER: THE CORE VIZ (6 Cols) */}
                <div className="col-span-6 flex flex-col gap-4 h-full">
                    {/* Map Visualizer */}
                    <div className="flex-[3] glass-panel rounded-[2rem] relative overflow-hidden group">
                        <Map
                            selectedCountry={selectedCountry}
                            onSelectCountry={setSelectedCountry}
                        />
                        <div className="absolute top-6 left-6 pointer-events-none">
                            <h3 className="text-2xl font-black tracking-tight">Supply Chain Core</h3>
                            <p className="text-xs text-muted-foreground font-medium uppercase tracking-widest">Real-time Global Nodes</p>
                        </div>
                    </div>

                    {/* Performance Analytics */}
                    <div className="flex-1 glass-panel rounded-[2rem] p-6">
                        <BottomPanel data={initialData} selectedCountry={selectedCountry} />
                    </div>
                </div>

                {/* 3. RIGHT: INTELLIGENCE PANEL (3 Cols) */}
                <div className="col-span-3 h-full overflow-hidden">
                    <ContextPanel selectedCountry={selectedCountry} />
                </div>

            </main>
        </div>
    );
}
'use client';

import React, { useEffect, useState } from 'react';
import { ContentCard } from '@/components/ui/ContentCard';
import { Zap, Activity, CheckCircle2, BrainCircuit, ArrowRight, ScanLine } from 'lucide-react';
import { getScannerStatus, getLiveMarketData } from '@/actions/getMarketData';
import { getDecisionHistory } from '@/actions/getDecisionHistory';

interface ContextPanelProps {
    selectedCountry: string | null;
}

export default function ContextPanel({ selectedCountry }: ContextPanelProps) {
    const [scannerData, setScannerData] = useState({ demand: 0, confidence: 0 });
    const [latestSignal, setLatestSignal] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    // Scanner Effect (Global Status)
    useEffect(() => {
        const fetchStatus = async () => {
            const data = await getScannerStatus();
            setScannerData(data);

            // Also fetch history for "Autonomous Scanner" log
            const hist = await getDecisionHistory();
            setHistory(hist);
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    // Decision Logic (Specific Material/Country)
    useEffect(() => {
        const fetchMaterialStatus = async () => {
            if (selectedCountry) {
                // In a real app, 'selectedCountry' might map to a region's material
                // For this demo, we'll map Country -> Random Material or Specific one
                // Let's grab the latest signal for "Copper" or similar as a proxy
                const marketData = await getLiveMarketData();
                // Find a material with a BUY signal if possible, else the first one
                const interesting = marketData.find(m => m.signal === 'BUY') || marketData[0];

                if (interesting) {
                    setLatestSignal({
                        signal: interesting.signal,
                        confidence: interesting.confidence || 90,
                        material: interesting.name,
                        price: interesting.price
                    });
                }
            }
        };

        fetchMaterialStatus();
        const interval = setInterval(fetchMaterialStatus, 3000); // Live update
        return () => clearInterval(interval);

    }, [selectedCountry]);

    return (
        <aside className="w-[350px] h-full p-4 bg-background/40 backdrop-blur-md border-l border-white/10 flex flex-col gap-4">

            {selectedCountry ? (
                // --- MODE A: DECISION ENGINE ---
                <div className="flex flex-col h-full animate-in fade-in slide-in-from-right duration-500">
                    <ContentCard className="flex-shrink-0 p-4 border-l-4 border-primary bg-gradient-to-br from-primary/10 to-transparent rounded-r-xl border-y border-r border-white/10">
                        <div className="flex items-center gap-3 mb-1">
                            <BrainCircuit className="text-primary" size={24} />
                            <h2 className="text-sm font-bold uppercase tracking-wider text-primary">Decision Engine</h2>
                        </div>
                        <div className="text-2xl font-black text-foreground">{selectedCountry}</div>
                    </ContentCard>

                    <div className="flex-1 flex flex-col gap-4 mt-4">
                        <ContentCard className="p-6 flex flex-col items-center justify-center border-white/5 bg-white/5 rounded-xl relative overflow-hidden">
                            <div className={`absolute inset-0 opacity-10 ${latestSignal?.signal === 'BUY' ? 'bg-secondary' : 'bg-orange-500'}`} />
                            <span className="text-xs font-bold text-muted-foreground mb-2 tracking-widest relative z-10">AI RECOMMENDATION</span>
                            <span className={`text-4xl font-black tracking-tighter relative z-10 ${latestSignal?.signal === 'BUY' ? 'text-secondary drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]' : 'text-orange-400'}`}>
                                {latestSignal?.signal || "ANALYZING..."}
                            </span>
                            {latestSignal && (
                                <span className="text-xs font-mono mt-2 text-white/50">{latestSignal.material} @ ${latestSignal.price}</span>
                            )}
                        </ContentCard>

                        <div className="grid grid-cols-2 gap-3">
                            <ContentCard className="flex flex-col items-center justify-center p-3 rounded-xl border-white/10">
                                <span className="text-[10px] text-muted-foreground uppercase font-bold">Confidence</span>
                                <span className="text-xl font-bold text-foreground">{latestSignal?.confidence || 0}%</span>
                            </ContentCard>
                            <ContentCard className="flex flex-col items-center justify-center p-3 rounded-xl border-white/10">
                                <span className="text-[10px] text-muted-foreground uppercase font-bold">Volatility</span>
                                <span className="text-xl font-bold text-foreground">{(latestSignal?.confidence || 0) > 90 ? 'LOW' : 'HIGH'}</span>
                            </ContentCard>
                        </div>

                        <ContentCard title="Recommended Actions" className="flex-1 rounded-xl border border-white/10 min-h-0">
                            <div className="space-y-2 overflow-y-auto custom-scrollbar p-1">
                                <button className="w-full flex items-center justify-between p-3 rounded-lg bg-primary/20 hover:bg-primary/30 text-primary-foreground transition-all border border-primary/20 text-xs font-bold group shadow-[0_0_20px_rgba(139,92,246,0.2)]">
                                    <span>INITIATE PROCUREMENT</span>
                                    <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                                </button>
                                <button className="w-full flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 text-foreground transition-colors border border-white/10 text-xs font-bold">
                                    <span>VIEW LOGISTICS ROUTE</span>
                                </button>
                            </div>
                        </ContentCard>
                    </div>
                </div>
            ) : (
                // --- MODE B: AUTONOMOUS SCANNER ---
                <div className="flex flex-col h-full animate-in fade-in duration-500">
                    <div className="flex items-center justify-between mb-4 px-1">
                        <span className="text-xs font-bold text-muted-foreground">AUTONOMOUS SCANNER</span>
                        <div className="flex items-center gap-2">
                            <span className="flex h-2 w-2 rounded-full bg-secondary animate-pulse" />
                            <span className="text-[10px] font-medium text-secondary">ACTIVE</span>
                        </div>
                    </div>

                    <div className="text-center mb-6">
                        <div className="relative inline-flex items-center justify-center mb-4">
                            <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
                            <ScanLine className="text-primary relative z-10" size={48} />
                        </div>
                        <span className="text-sm font-bold text-primary block animate-pulse">Scanning Global Markets...</span>
                    </div>

                    <div className="grid grid-cols-1 gap-4 mb-4">
                        <ContentCard className="flex flex-col p-4 border-dashed rounded-xl border-white/20">
                            <div className="flex items-center gap-2 mb-2">
                                <Activity className="w-4 h-4 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground uppercase font-bold">Detected Demand</span>
                            </div>
                            <span className="text-3xl font-mono font-bold text-foreground">{scannerData.demand.toLocaleString()} T</span>
                        </ContentCard>

                        <ContentCard className="flex flex-col p-4 border-dashed rounded-xl border-white/20">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle2 className="w-4 h-4 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground uppercase font-bold">Model Confidence</span>
                            </div>
                            <span className="text-3xl font-mono font-bold text-secondary">{scannerData.confidence}%</span>
                        </ContentCard>
                    </div>

                    <ContentCard title="Recent Decisions (Live DB)" className="flex-1 rounded-xl border border-white/10 min-h-0 bg-black/20">
                        <div className="font-mono text-[10px] space-y-2 p-2 h-full overflow-y-auto custom-scrollbar text-muted-foreground">
                            {history.length === 0 && <p className="animate-pulse">{`> WAITING FOR SIGNALS...`}</p>}

                            {history.map((record, i) => (
                                <div key={i} className="flex flex-col border-b border-white/5 pb-1 mb-1 last:border-0">
                                    <div className="flex justify-between">
                                        <span className="text-white/80 font-bold">{record.material}</span>
                                        <span className={record.signal === 'BUY' ? 'text-secondary' : 'text-orange-400'}>{record.signal}</span>
                                    </div>
                                    <div className="flex justify-between opacity-50">
                                        <span>${record.price.toFixed(2)}</span>
                                        <span>{new Date(record.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </ContentCard>
                </div>
            )}
        </aside>
    );
}

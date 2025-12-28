import React from 'react';
import { MaterialData } from '@/actions/getMarketData';
import { ContentCard } from '@/components/ui/ContentCard';
import MiniGraph from './MiniGraph';

export default function BottomPanel({ data, selectedCountry }: { data: MaterialData[], selectedCountry: string | null }) {
    // Generate mock history for sparklines
    const getSparkline = (base: number) => Array.from({ length: 20 }, () => base + (Math.random() - 0.5) * (base * 0.05));

    return (
        <section className="flex-[3] w-full p-4 flex gap-4 min-h-0 bg-background/50 backdrop-blur-sm border-t border-border">

            {/* CARD 1: FORECASTS */}
            <ContentCard title="Price Forecasts (30D)" className="flex-1 rounded-xl shadow-sm border border-border/50">
                <div className="w-full h-full flex items-center justify-center p-2">
                    {/* Mock multi-line chart feeling */}
                    <div className="w-full h-full grid grid-cols-2 gap-4">
                        {data.slice(0, 2).map((item, i) => (
                            <div key={item.name} className="flex flex-col h-full justify-end">
                                <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">{item.name}</div>
                                <div className="h-24 w-full">
                                    <MiniGraph data={getSparkline(item.price)} color={i === 0 ? "#10b981" : "#3b82f6"} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </ContentCard>

            {/* CARD 2: REGIONAL DEMAND */}
            <ContentCard title="Regional Demand (Live)" className="flex-1 rounded-xl shadow-sm border border-border/50">
                <div className="w-full h-full p-2 flex flex-col gap-2 overflow-y-auto custom-scrollbar">
                    {data.map((item, i) => (
                        <div key={item.name} className="flex items-center gap-2 text-xs">
                            <span className="w-16 font-mono text-muted-foreground">{item.name.substring(0, 3).toUpperCase()}</span>
                            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary/80 rounded-full"
                                    style={{ width: `${Math.random() * 60 + 20}%` }}
                                />
                            </div>
                            <span className="font-bold text-foreground">{(Math.random() * 1000).toFixed(0)}T</span>
                        </div>
                    ))}
                </div>
            </ContentCard>
        </section>
    );
}

import React from 'react';
import { ContentCard } from '@/components/ui/ContentCard';
import { MaterialData } from '@/actions/getMarketData';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

export default function LeftPanel({ data, selectedCountry }: { data: MaterialData[], selectedCountry: string | null }) {
    return (
        <aside className="w-[300px] h-full flex flex-col p-4 bg-background/50 backdrop-blur-sm overflow-y-auto space-y-3 no-scrollbar border-r border-border">
            <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1 px-1">Global Materials</h2>

            {data.map((item) => (
                <ContentCard key={item.name} className="flex-shrink-0 p-3 rounded-xl border border-border/50 hover:border-primary/50 transition-colors group">
                    <div className="flex justify-between items-start mb-2">
                        <span className="font-bold text-sm group-hover:text-primary transition-colors">{item.name}</span>
                        {item.trend > 0 ? (
                            <ArrowUpRight className="text-emerald-500" size={16} />
                        ) : item.trend < 0 ? (
                            <ArrowDownRight className="text-red-500" size={16} />
                        ) : (
                            <Minus className="text-muted-foreground" size={16} />
                        )}
                    </div>

                    <div className="flex items-end justify-between">
                        <div className="text-xl font-mono font-bold">
                            ${item.price.toLocaleString()}
                        </div>
                        <div className={`text-xs font-bold ${item.trend >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                            {item.trend > 0 ? '+' : ''}{item.trend}%
                        </div>
                    </div>

                    {/* Simulated small progress or demand indicator */}
                    <div className="mt-3 h-1 w-full bg-muted rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full ${item.trend >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.random() * 40 + 30}%` }}
                        />
                    </div>
                </ContentCard>
            ))}
        </aside>
    );
}

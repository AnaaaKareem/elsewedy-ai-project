'use client';

import React, { useState, useEffect } from 'react';
import { Moon, Sun, Cpu, Bell, Settings } from 'lucide-react';

export default function Header() {
    const [dark, setDark] = useState(true);

    // Sync theme with the document class for Tailwind 'dark' selector
    useEffect(() => {
        if (dark) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [dark]);

    return (
        <header className="h-20 w-full border-b border-white/10 glass-panel flex items-center justify-between px-8 sticky top-0 z-[100]">
            {/* LEFT: Branding */}
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                    {/* Elsewedy Electric Visual Identity */}
                    <div className="relative group">
                        <div className="absolute -inset-1 bg-red-600 rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                        <div className="relative w-10 h-10 bg-red-600 rounded-lg flex items-center justify-center font-black text-white text-xl shadow-lg">
                            E
                        </div>
                    </div>

                    <div className="flex flex-col">
                        <span className="text-lg font-black tracking-tighter leading-none text-foreground">
                            ELSEWEDY
                        </span>
                        <span className="text-[10px] font-bold tracking-[0.3em] text-muted-foreground leading-none mt-1">
                            ELECTRIC
                        </span>
                    </div>
                </div>

                {/* Status Divider */}
                <div className="h-8 w-[1px] bg-border/50 mx-2" />

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20">
                        <Cpu size={14} className="text-primary animate-pulse" />
                        <span className="text-[10px] font-bold text-primary uppercase tracking-widest">
                            AI Market Core Active
                        </span>
                    </div>
                </div>
            </div>

            {/* RIGHT: Actions */}
            <div className="flex items-center gap-3">
                <div className="flex items-center gap-1 mr-4">
                    <button className="p-2.5 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-xl transition-colors relative">
                        <Bell size={18} />
                        <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-background" />
                    </button>
                    <button className="p-2.5 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-xl transition-colors">
                        <Settings size={18} />
                    </button>
                </div>

                <button
                    onClick={() => setDark(!dark)}
                    className="flex items-center gap-3 px-4 py-2 rounded-2xl glass-card hover:scale-[1.02] active:scale-[0.98] transition-all group"
                >
                    <div className="flex flex-col items-end">
                        <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-tight leading-none">Theme</span>
                        <span className="text-[11px] font-bold text-foreground leading-none mt-1">
                            {dark ? 'Deep Space' : 'Pure Light'}
                        </span>
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-background flex items-center justify-center border border-white/10 group-hover:border-primary/50 transition-colors">
                        {dark ? (
                            <Sun size={16} className="text-yellow-400 fill-yellow-400/20" />
                        ) : (
                            <Moon size={16} className="text-indigo-600 fill-indigo-600/10" />
                        )}
                    </div>
                </button>
            </div>
        </header>
    );
}
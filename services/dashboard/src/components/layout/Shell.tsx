'use client';

import React from 'react';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function Shell({ children }: { children: React.ReactNode }) {
    return (
        <div className="min-h-screen w-full bg-background font-sans text-foreground selection:bg-primary/30 relative overflow-hidden">

            {/* AMBIENT BACKGROUND BLOBS */}
            <div className="fixed top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[120px] rounded-full mix-blend-multiply dark:mix-blend-screen opacity-60 animate-blob pointer-events-none" />
            <div className="fixed bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-secondary/60 blur-[120px] rounded-full mix-blend-multiply dark:mix-blend-screen opacity-60 animate-blob animation-delay-2000 pointer-events-none" />
            <div className="fixed top-[20%] right-[20%] w-[30%] h-[30%] bg-pink-300/30 dark:bg-pink-900/20 blur-[100px] rounded-full mix-blend-multiply dark:mix-blend-screen opacity-60 animate-blob animation-delay-4000 pointer-events-none" />

            <div className="flex h-screen flex-col relative z-10">
                {/* Floating Glass Header */}
                <header className="mx-6 mt-4 flex h-16 items-center justify-between rounded-full border border-white/20 bg-white/40 dark:bg-black/20 backdrop-blur-xl shadow-soft px-8 transition-all hover:bg-white/50 dark:hover:bg-black/30">
                    <div className="flex items-center gap-4">
                        {/* Image Logo with Fallback */}
                        <div className="relative h-8 w-40 flex items-center justify-start">
                            <img
                                src="/logo.png"
                                alt="Elsewedy Electric"
                                className="h-full w-auto object-contain dark:invert"
                                onError={(e) => {
                                    e.currentTarget.style.display = 'none';
                                    e.currentTarget.nextElementSibling?.classList.remove('hidden');
                                }}
                            />
                            <svg className="hidden h-6 w-auto text-primary" viewBox="0 0 300 50" fill="currentColor">
                                <path d="M20 25a12 12 0 1 1 24 0 12 12 0 0 1-24 0Z" className="animate-pulse" />
                                <text x="50" y="32" fontFamily="Arial, sans-serif" fontSize="24" fontWeight="900" letterSpacing="1">ELSEWEDY<tspan fill="gray">ELEC</tspan></text>
                            </svg>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <button className="h-9 w-9 rounded-full bg-secondary hover:bg-secondary/80 flex items-center justify-center text-xs font-bold ring-2 ring-background transition-colors shadow-sm">
                            KA
                        </button>
                    </div>
                </header>

                {/* MAIN CONTENT */}
                <main className="flex-1 flex overflow-hidden relative mt-4 mx-6 mb-6 rounded-[2rem] border border-white/20 bg-white/30 dark:bg-black/10 backdrop-blur-md shadow-soft">
                    {children}
                </main>
            </div>
        </div>
    );
}

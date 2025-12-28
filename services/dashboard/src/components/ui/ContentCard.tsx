import React from 'react';

// Replaces GlassCard with a cleaner, semantic styled card
interface ContentCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    action?: React.ReactNode;
}

export function ContentCard({ title, children, className }: any) {
    return (
        <div className={`glass-card rounded-[1.5rem] flex flex-col ${className}`}>
            {title && (
                <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
                    <h3 className="text-[11px] font-extrabold uppercase tracking-[0.15em] text-muted-foreground">
                        {title}
                    </h3>
                    <div className="w-1.5 h-1.5 rounded-full bg-primary/40 shadow-[0_0_8px_var(--primary)]" />
                </div>
            )}
            <div className="p-5 flex-1">{children}</div>
        </div>
    );
}

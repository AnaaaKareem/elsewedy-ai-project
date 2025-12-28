'use client';

import React from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface MiniGraphProps {
    color: string;
    data: number[];
}

export default function MiniGraph({ color, data }: MiniGraphProps) {
    const chartData = data.map((val, i) => ({ i, val }));

    return (
        <div className="h-[40px] w-full select-none pointer-events-none">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                    <Line
                        type="monotone"
                        dataKey="val"
                        stroke={color}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={true}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

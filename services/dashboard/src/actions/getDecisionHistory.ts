'use server'

import pool from '@/lib/db';

export interface DecisionRecord {
    id: number;
    material: string;
    country: string;
    price: number;
    prediction: number;
    signal: string;
    timestamp: string;
}

export async function getDecisionHistory(): Promise<DecisionRecord[]> {
    try {
        // Fetch last 10 decisions
        // Mapped to match python's 'ai_signals' table schema
        const query = `
            SELECT 
                s.created_at as timestamp, 
                m.name as material, 
                c.name as country, 
                s.input_price as price, 
                s.predicted_demand as prediction, 
                s.decision as signal
            FROM ai_signals s
            JOIN materials m ON s.material_id = m.id
            JOIN countries c ON s.country_id = c.id
            ORDER BY s.created_at DESC 
            LIMIT 10
        `;

        const res = await pool.query(query);

        return res.rows.map(row => ({
            ...row,
            price: parseFloat(row.price),
            prediction: parseFloat(row.prediction),
            timestamp: row.timestamp.toISOString() // Serialize for client
        }));

    } catch (error) {
        console.error("Failed to fetch decision history:", error);
        return [];
    }
}

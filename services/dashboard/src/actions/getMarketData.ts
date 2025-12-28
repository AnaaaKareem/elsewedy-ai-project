'use server'

import redis from '@/lib/redis';

const MATERIALS = [
    "Copper", "Aluminum", "XLPE Polymer", "PVC Compound",
    "Mica Tape", "Steel Tape", "Lead Ingots", "Masterbatch"
];

export interface MaterialData {
    name: string;
    price: number;
    trend: number;
    signal: string;
    forecast: number;
    confidence?: number;
}

export async function getLiveMarketData(): Promise<MaterialData[]> {
    try {
        const pipeline = redis.pipeline();

        // For each material, fetch relevant keys (Defaulting to Egypt for now)
        // TODO: Accept country as parameter
        MATERIALS.forEach(mat => {
            const country = "Egypt";
            pipeline.get(`live:${country}:${mat}:price`);
            pipeline.get(`live:${country}:${mat}:trend`);
            pipeline.get(`live:${country}:${mat}:signal`);
            pipeline.get(`live:${country}:${mat}:forecast`);
            pipeline.get(`live:${country}:${mat}:confidence`);
        });

        const results = await pipeline.exec();

        // Check if we actually got results (Redis might be null if keys don't exist)
        const hasData = results && results.length > 0 && results[0][1] !== null;

        if (!hasData) {
            console.warn("No data in Redis, serving fallback mock data.");
            return getMockData();
        }

        const data: MaterialData[] = [];

        // Parse results (5 keys per material now)
        for (let i = 0; i < MATERIALS.length; i++) {
            const baseIdx = i * 5;

            // Helper to safely parse result
            const parseRes = (idx: number, isFloat = false) => {
                const [err, val] = results![idx];
                if (err || val === null) return isFloat ? 0 : "N/A";
                return isFloat ? parseFloat(val as string) : (val as string);
            };

            data.push({
                name: MATERIALS[i],
                price: parseRes(baseIdx, true) as number,
                trend: 0,
                signal: parseRes(baseIdx + 2) as string,
                forecast: parseRes(baseIdx + 3, true) as number,
                confidence: parseRes(baseIdx + 4, true) as number,
            });
        }


        return data;

    } catch (error) {
        console.error("Redis Connection Failed:", error);
        return getMockData();
    }
}

function getMockData(): MaterialData[] {
    return MATERIALS.map(mat => ({
        name: mat,
        price: Math.floor(Math.random() * 5000) + 1000,
        trend: Math.random() * 5,
        signal: Math.random() > 0.5 ? "BUY" : "WAIT",
        forecast: Math.floor(Math.random() * 6000) + 1000,
        confidence: 85
    }));
}

export async function getScannerStatus() {
    // [REAL] Aggregate confidence from all live materials
    const materials = await getLiveMarketData();

    // Calculate average confidence (default to 85 if no data)
    const totalConf = materials.reduce((acc, curr) => acc + (curr.confidence || 85), 0);
    const avgConf = Math.floor(totalConf / (materials.length || 1));

    return {
        demand: Math.floor(10000 + Math.random() * 90000), // Still simulated for now (Region data is complex)
        confidence: avgConf
    }
}

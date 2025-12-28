import React from 'react';
import Shell from '@/components/layout/Shell';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { getLiveMarketData } from '@/actions/getMarketData';

export const dynamic = 'force-dynamic'; // Ensure no caching for live data

export default async function Page() {
    const data = await getLiveMarketData();

    return (
        <Shell>
            <DashboardLayout initialData={data} />
        </Shell>
    );
}

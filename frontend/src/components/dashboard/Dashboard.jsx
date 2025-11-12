import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

const Dashboard = ({ health }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await api.get('/dashboard/stats');
                setStats(response.data);
            } catch (error) {
                setError(error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error.message}</div>;
    }

    return (
        <div>
            <h1>Dashboard</h1>
            <div>
                <h2>Open Positions: {stats.open_positions}</h2>
                <h2>Total Positions: {stats.total_positions}</h2>
                <h2>PnL: {stats.pnl}</h2>
            </div>
        </div>
    );
};

export default Dashboard;

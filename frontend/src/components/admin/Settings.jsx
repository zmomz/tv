import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

const Settings = () => {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const response = await api.get('/config');
                setConfig(response.data);
            } catch (error) {
                setError(error);
            } finally {
                setLoading(false);
            }
        };

        fetchConfig();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        const [section, key] = name.split('.');
        setConfig({
            ...config,
            [section]: {
                ...config[section],
                [key]: value,
            },
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await api.put('/config', config);
            alert('Settings saved successfully!');
        } catch (error) {
            setError(error);
            alert('Failed to save settings.');
        }
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error.message}</div>;
    }

    return (
        <div>
            <h1>Settings</h1>
            <form onSubmit={handleSubmit}>
                <h2>App</h2>
                <label>
                    Mode:
                    <input
                        type="text"
                        name="app.mode"
                        value={config.app.mode}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    Data Directory:
                    <input
                        type="text"
                        name="app.data_dir"
                        value={config.app.data_dir}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    Log Level:
                    <input
                        type="text"
                        name="app.log_level"
                        value={config.app.log_level}
                        onChange={handleInputChange}
                    />
                </label>

                <h2>Exchange</h2>
                <label>
                    Name:
                    <input
                        type="text"
                        name="exchange.name"
                        value={config.exchange.name}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    API Key:
                    <input
                        type="text"
                        name="exchange.api_key"
                        value={config.exchange.api_key}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    API Secret:
                    <input
                        type="password"
                        name="exchange.api_secret"
                        value={config.exchange.api_secret}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    Testnet:
                    <input
                        type="checkbox"
                        name="exchange.testnet"
                        checked={config.exchange.testnet}
                        onChange={(e) =>
                            handleInputChange({
                                target: {
                                    name: e.target.name,
                                    value: e.target.checked,
                                },
                            })
                        }
                    />
                </label>
                <label>
                    Precision Refresh (sec):
                    <input
                        type="number"
                        name="exchange.precision_refresh_sec"
                        value={config.exchange.precision_refresh_sec}
                        onChange={handleInputChange}
                    />
                </label>

                <h2>Execution Pool</h2>
                <label>
                    Max Open Groups:
                    <input
                        type="number"
                        name="execution_pool.max_open_groups"
                        value={config.execution_pool.max_open_groups}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    Count Pyramids:
                    <input
                        type="checkbox"
                        name="execution_pool.count_pyramids"
                        checked={config.execution_pool.count_pyramids}
                        onChange={(e) =>
                            handleInputChange({
                                target: {
                                    name: e.target.name,
                                    value: e.target.checked,
                                },
                            })
                        }
                    />
                </label>

                <h2>Grid Strategy</h2>
                {/* TODO: Add inputs for dca_config and tp_config */}

                <h2>Risk Engine</h2>
                <label>
                    Loss Threshold (%):
                    <input
                        type="number"
                        name="risk_engine.loss_threshold_percent"
                        value={config.risk_engine.loss_threshold_percent}
                        onChange={handleInputChange}
                    />
                </label>
                <label>
                    Require Full Pyramids:
                    <input
                        type="checkbox"
                        name="risk_engine.require_full_pyramids"
                        checked={config.risk_engine.require_full_pyramids}
                        onChange={(e) =>
                            handleInputChange({
                                target: {
                                    name: e.target.name,
                                    value: e.target.checked,
                                },
                            })
                        }
                    />
                </label>
                <label>
                    Post Full Wait (min):
                    <input
                        type="number"
                        name="risk_engine.post_full_wait_minutes"
                        value={config.risk_engine.post_full_wait_minutes}
                        onChange={handleInputChange}
                    />
                </label>

                <button type="submit">Save</button>
            </form>
        </div>
    );
};

export default Settings;

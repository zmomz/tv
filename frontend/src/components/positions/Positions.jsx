import React from 'react';

const Positions = ({ positions }) => {
    if (!positions) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>Positions</h1>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Status</th>
                        <th>Entry Price</th>
                        <th>Current Price</th>
                        <th>PnL</th>
                    </tr>
                </thead>
                <tbody>
                    {positions.map((position) => (
                        <tr key={position.id}>
                            <td>{position.symbol}</td>
                            <td>{position.status}</td>
                            <td>{position.entry_price}</td>
                            <td>{position.current_price}</td>
                            <td>{position.pnl}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Positions;

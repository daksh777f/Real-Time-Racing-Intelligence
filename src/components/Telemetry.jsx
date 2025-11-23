import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';

const data = [
    { time: '0s', speed: 0, rpm: 0 },
    { time: '10s', speed: 120, rpm: 4000 },
    { time: '20s', speed: 200, rpm: 8000 },
    { time: '30s', speed: 280, rpm: 11000 },
    { time: '40s', speed: 310, rpm: 12000 },
    { time: '50s', speed: 150, rpm: 6000 },
    { time: '60s', speed: 250, rpm: 10000 },
];

const Telemetry = () => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="w-full max-w-4xl mx-auto mt-12 p-6 glass-card rounded-2xl relative z-10"
        >
            <h3 className="text-xl font-mono text-neon-blue mb-6 tracking-widest uppercase">Live Telemetry</h3>

            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="time" stroke="#666" />
                        <YAxis stroke="#666" />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                            itemStyle={{ color: '#fff' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="speed"
                            stroke="#00f3ff"
                            strokeWidth={3}
                            dot={{ r: 4, fill: '#00f3ff' }}
                            activeDot={{ r: 8, fill: '#fff' }}
                            animationDuration={2000}
                        />
                        <Line
                            type="monotone"
                            dataKey="rpm"
                            stroke="#ff003c"
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={false}
                            animationDuration={2000}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </motion.div>
    );
};

export default Telemetry;

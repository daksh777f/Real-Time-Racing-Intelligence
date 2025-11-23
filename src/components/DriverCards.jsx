import React from 'react';
import { motion } from 'framer-motion';

const drivers = [
    { id: 1, name: "Max Verstappen", team: "Red Bull", speed: "320 km/h", tire: "Soft", color: "border-neon-blue" },
    { id: 2, name: "Lewis Hamilton", team: "Mercedes", speed: "318 km/h", tire: "Medium", color: "border-neon-purple" },
    { id: 3, name: "Charles Leclerc", team: "Ferrari", speed: "319 km/h", tire: "Hard", color: "border-neon-red" },
];

const DriverCards = () => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl mx-auto mt-12 px-4 relative z-10">
            {drivers.map((driver, index) => (
                <motion.div
                    key={driver.id}
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.2 }}
                    whileHover={{
                        scale: 1.05,
                        rotateX: 5,
                        rotateY: 5,
                        boxShadow: "0 0 30px rgba(0, 243, 255, 0.2)"
                    }}
                    className={`glass-card p-6 rounded-xl border-t-4 ${driver.color} transform transition-all duration-300`}
                >
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-2xl font-bold font-mono">{driver.name}</h3>
                            <p className="text-gray-400 text-sm uppercase tracking-wider">{driver.team}</p>
                        </div>
                        <div className="text-right">
                            <span className="text-3xl font-mono font-bold text-white">{driver.id}</span>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <div className="flex justify-between items-center bg-white/5 p-2 rounded">
                            <span className="text-xs text-gray-400 uppercase">Top Speed</span>
                            <span className="font-mono text-neon-lime">{driver.speed}</span>
                        </div>
                        <div className="flex justify-between items-center bg-white/5 p-2 rounded">
                            <span className="text-xs text-gray-400 uppercase">Tire Compound</span>
                            <span className="font-mono text-white">{driver.tire}</span>
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    );
};

export default DriverCards;

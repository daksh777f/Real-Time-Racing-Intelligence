import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';

const InputPanel = ({ onGenerate }) => {
    const [jsonInput, setJsonInput] = useState('');

    const handleGenerate = () => {
        try {
            const parsed = JSON.parse(jsonInput);
            onGenerate(parsed);
        } catch (e) {
            alert('Invalid JSON');
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="w-full max-w-4xl mx-auto p-6 glass-card rounded-2xl relative z-10"
        >
            <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-8 bg-neon-lime rounded-full" />
                <h2 className="text-2xl font-mono font-bold text-white">RACE DATA INPUT</h2>
            </div>

            <textarea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                placeholder="Paste race telemetry JSON here..."
                className="w-full h-40 bg-dark-bg/50 border border-white/10 rounded-xl p-4 text-neon-blue font-mono focus:outline-none focus:border-neon-blue transition-colors resize-none"
            />

            <div className="flex justify-end mt-4">
                <motion.button
                    whileHover={{ scale: 1.05, boxShadow: "0 0 20px rgba(204, 255, 0, 0.3)" }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleGenerate}
                    className="bg-neon-lime text-black font-bold py-3 px-8 rounded-xl flex items-center gap-2 font-mono uppercase tracking-wider"
                >
                    <Zap className="w-5 h-5" />
                    Generate Insights
                </motion.button>
            </div>
        </motion.div>
    );
};

export default InputPanel;

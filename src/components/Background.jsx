import React from 'react';
import { motion } from 'framer-motion';

const Background = () => {
    return (
        <div className="fixed inset-0 z-0 overflow-hidden bg-dark-bg pointer-events-none">
            {/* Grid Pattern */}
            <div className="absolute inset-0 bg-grid-pattern opacity-20 transform perspective-1000 rotate-x-60 scale-150 origin-top" />

            {/* Glowing Orbs */}
            <motion.div
                animate={{
                    opacity: [0.3, 0.6, 0.3],
                    scale: [1, 1.2, 1],
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-[-20%] left-[20%] w-[600px] h-[600px] bg-neon-blue/20 rounded-full blur-[120px]"
            />
            <motion.div
                animate={{
                    opacity: [0.2, 0.5, 0.2],
                    scale: [1, 1.3, 1],
                }}
                transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                className="absolute bottom-[-20%] right-[10%] w-[500px] h-[500px] bg-neon-purple/20 rounded-full blur-[100px]"
            />

            {/* Vignette */}
            <div className="absolute inset-0 bg-radial-gradient from-transparent to-dark-bg/90" />

            {/* Scanlines */}
            <div className="absolute inset-0 bg-[url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')] opacity-[0.03] pointer-events-none" />
        </div>
    );
};

export default Background;

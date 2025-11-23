import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare } from 'lucide-react';

const Commentary = ({ comments = [] }) => {
    const [displayComments, setDisplayComments] = useState([]);

    useEffect(() => {
        if (comments.length > 0) {
            setDisplayComments(comments);
        } else {
            // Demo data
            const demoComments = [
                "Verstappen setting purple sectors in Sector 2.",
                "Hamilton reporting tire degradation on softs.",
                "Safety car deployed due to debris on turn 4.",
            ];
            setDisplayComments(demoComments);
        }
    }, [comments]);

    return (
        <div className="w-full max-w-4xl mx-auto mt-8 p-6 glass-card rounded-2xl relative z-10">
            <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-2">
                <MessageSquare className="text-neon-blue w-5 h-5" />
                <h3 className="text-xl font-mono text-neon-blue tracking-widest">AI COMMENTARY STREAM</h3>
            </div>

            <div className="space-y-3 h-48 overflow-y-auto pr-2 custom-scrollbar">
                <AnimatePresence>
                    {displayComments.map((comment, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0 }}
                            transition={{ delay: index * 0.5 }}
                            className="p-3 bg-white/5 rounded-lg border-l-2 border-neon-blue"
                        >
                            <p className="font-mono text-sm text-gray-300">
                                <span className="text-neon-blue mr-2">[{new Date().toLocaleTimeString()}]</span>
                                {comment}
                            </p>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default Commentary;

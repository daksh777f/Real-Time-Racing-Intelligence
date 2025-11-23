import React from 'react';
import { motion } from 'framer-motion';
import { Activity, BarChart2, Map, Settings } from 'lucide-react';

const Navbar = () => {
    const navItems = [
        { name: 'Telemetry', icon: Activity },
        { name: 'Track Map', icon: Map },
        { name: 'Analysis', icon: BarChart2 },
        { name: 'Settings', icon: Settings },
    ];

    return (
        <motion.nav
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="fixed top-0 left-0 right-0 z-50 px-6 py-4 flex justify-between items-center"
        >
            {/* Logo */}
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-neon-red rounded-br-xl rounded-tl-xl transform skew-x-[-10deg]" />
                <span className="text-2xl font-mono font-bold tracking-tighter text-white">
                    RACE<span className="text-neon-blue">MATE</span>
                </span>
            </div>

            {/* Navigation */}
            <div className="hidden md:flex items-center gap-8 glass px-8 py-3 rounded-full">
                {navItems.map((item, index) => (
                    <motion.a
                        key={item.name}
                        href="#"
                        whileHover={{ scale: 1.1, color: '#00f3ff' }}
                        className="flex items-center gap-2 text-sm font-mono text-gray-300 hover:text-white transition-colors"
                    >
                        <item.icon className="w-4 h-4" />
                        <span>{item.name}</span>
                    </motion.a>
                ))}
            </div>

            {/* User Profile / Status */}
            <div className="flex items-center gap-4">
                <div className="hidden md:block text-right">
                    <p className="text-xs text-gray-400 uppercase tracking-widest">System Status</p>
                    <p className="text-neon-lime font-mono text-sm">ONLINE</p>
                </div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-neon-blue to-neon-purple p-[2px]">
                    <div className="w-full h-full rounded-full bg-dark-bg flex items-center justify-center">
                        <span className="font-bold text-xs">RM</span>
                    </div>
                </div>
            </div>
        </motion.nav>
    );
};

export default Navbar;

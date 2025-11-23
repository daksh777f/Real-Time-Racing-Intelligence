import React, { useState, useRef } from 'react';
import Background from './components/Background';
import Hero from './components/Hero';
import InputPanel from './components/InputPanel';
import Commentary from './components/Commentary';
import DriverCards from './components/DriverCards';
import Telemetry from './components/Telemetry';
import TrackMap from './components/TrackMap';
import Navbar from './components/Navbar';
import SpeedometerBackground from './components/SpeedometerBackground';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [showDashboard, setShowDashboard] = useState(false);
  const dashboardRef = useRef(null);

  const handleGenerate = (data) => {
    console.log("Data received:", data);
    setShowDashboard(true);
    setTimeout(() => {
      dashboardRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <div className="min-h-screen text-white font-sans selection:bg-neon-blue selection:text-black">
      <Background />
      <SpeedometerBackground />
      <Navbar />

      <div className="relative z-10">
        <Hero />

        <div className="container mx-auto px-4 py-20 space-y-20">
          <InputPanel onGenerate={handleGenerate} />

          <AnimatePresence>
            {showDashboard && (
              <motion.div
                ref={dashboardRef}
                initial={{ opacity: 0, y: 100 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="space-y-20 pb-20"
              >
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <Commentary />
                  <TrackMap />
                </div>

                <DriverCards />
                <Telemetry />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default App;

import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { MotionPathPlugin } from 'gsap/MotionPathPlugin';

gsap.registerPlugin(MotionPathPlugin);

const TrackMap = () => {
    const trackRef = useRef(null);
    const car1Ref = useRef(null);
    const car2Ref = useRef(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Car 1 Animation
            gsap.to(car1Ref.current, {
                motionPath: {
                    path: "#track-path",
                    align: "#track-path",
                    autoRotate: true,
                    alignOrigin: [0.5, 0.5],
                },
                duration: 12,
                repeat: -1,
                ease: "none",
            });

            // Car 2 Animation (Offset)
            gsap.to(car2Ref.current, {
                motionPath: {
                    path: "#track-path",
                    align: "#track-path",
                    autoRotate: true,
                    alignOrigin: [0.5, 0.5],
                    start: 0.1,
                    end: 1.1,
                },
                duration: 11.5, // Slightly faster to simulate overtaking
                repeat: -1,
                ease: "none",
            });
        }, trackRef);

        return () => ctx.revert();
    }, []);

    return (
        <div ref={trackRef} className="w-full max-w-4xl mx-auto mt-12 p-6 glass-card rounded-2xl relative z-10 flex flex-col items-center">
            <h3 className="text-xl font-mono text-neon-lime mb-6 tracking-widest uppercase">Live Track Position</h3>

            <div className="relative w-full h-[400px] flex items-center justify-center">
                <svg viewBox="0 0 800 400" className="w-full h-full overflow-visible">
                    {/* Track Path */}
                    <path
                        id="track-path"
                        d="M100,200 C100,100 300,50 400,200 C500,350 700,300 700,200 C700,100 500,50 400,100 C300,150 100,300 100,200 Z"
                        fill="none"
                        stroke="#333"
                        strokeWidth="20"
                        strokeLinecap="round"
                    />
                    <path
                        d="M100,200 C100,100 300,50 400,200 C500,350 700,300 700,200 C700,100 500,50 400,100 C300,150 100,300 100,200 Z"
                        fill="none"
                        stroke="#00f3ff"
                        strokeWidth="2"
                        strokeDasharray="10 10"
                        className="animate-pulse"
                    />

                    {/* Cars */}
                    <circle ref={car1Ref} r="8" fill="#ff003c" className="filter drop-shadow-[0_0_8px_rgba(255,0,60,0.8)]" />
                    <circle ref={car2Ref} r="8" fill="#ccff00" className="filter drop-shadow-[0_0_8px_rgba(204,255,0,0.8)]" />
                </svg>
            </div>
        </div>
    );
};

export default TrackMap;

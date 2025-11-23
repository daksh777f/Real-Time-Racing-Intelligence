import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

const SpeedometerBackground = () => {
    const needleRef = useRef(null);
    const containerRef = useRef(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Idle animation
            gsap.to(needleRef.current, {
                rotation: 40,
                duration: 2,
                repeat: -1,
                yoyo: true,
                ease: "sine.inOut",
            });

            // Mouse interaction
            const handleMouseMove = (e) => {
                const { clientX } = e;
                const width = window.innerWidth;
                const percentage = clientX / width;
                const rotation = -90 + (percentage * 180); // -90 to 90 degrees

                gsap.to(needleRef.current, {
                    rotation: rotation,
                    duration: 1,
                    overwrite: true,
                    ease: "power2.out",
                });
            };

            window.addEventListener('mousemove', handleMouseMove);
            return () => window.removeEventListener('mousemove', handleMouseMove);
        }, containerRef);

        return () => ctx.revert();
    }, []);

    return (
        <div ref={containerRef} className="fixed inset-0 z-0 pointer-events-none flex items-center justify-center opacity-10">
            <svg viewBox="0 0 400 200" className="w-[80vw] h-[40vw] max-w-[1000px]">
                {/* Gauge Arc */}
                <path
                    d="M 20 200 A 180 180 0 0 1 380 200"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white"
                    strokeDasharray="10 10"
                />
                <path
                    d="M 40 200 A 160 160 0 0 1 360 200"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="20"
                    className="text-neon-blue"
                    opacity="0.2"
                />

                {/* Ticks */}
                {[...Array(9)].map((_, i) => (
                    <line
                        key={i}
                        x1="200"
                        y1="200"
                        x2="200"
                        y2="40"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="text-white"
                        transform={`rotate(${-90 + (i * 22.5)} 200 200)`}
                        strokeDasharray="5 155"
                    />
                ))}

                {/* Needle */}
                <g ref={needleRef} transform="rotate(-90 200 200)">
                    <path
                        d="M 200 200 L 200 50"
                        stroke="#ff003c"
                        strokeWidth="4"
                        strokeLinecap="round"
                        className="filter drop-shadow-[0_0_10px_rgba(255,0,60,0.8)]"
                    />
                    <circle cx="200" cy="200" r="10" fill="#ff003c" />
                </g>
            </svg>
        </div>
    );
};

export default SpeedometerBackground;

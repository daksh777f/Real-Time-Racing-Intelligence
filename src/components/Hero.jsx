import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { MotionPathPlugin } from 'gsap/MotionPathPlugin';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowDown } from 'lucide-react';

gsap.registerPlugin(MotionPathPlugin, ScrollTrigger);

const Hero = () => {
    const containerRef = useRef(null);
    const textRef = useRef(null);
    const carRef = useRef(null);

    useEffect(() => {
        const ctx = gsap.context(() => {
            // Text Reveal
            gsap.from(textRef.current.children, {
                y: 100,
                opacity: 0,
                duration: 1.5,
                stagger: 0.2,
                ease: "power4.out",
            });

            // Car Animation
            gsap.to(carRef.current, {
                motionPath: {
                    path: "#hero-path",
                    align: "#hero-path",
                    autoRotate: true,
                    alignOrigin: [0.5, 0.5],
                },
                duration: 10,
                repeat: -1,
                ease: "none",
            });

            // Parallax Effect
            const handleMouseMove = (e) => {
                const { clientX, clientY } = e;
                const x = (clientX / window.innerWidth - 0.5) * 50;
                const y = (clientY / window.innerHeight - 0.5) * 50;

                gsap.to(textRef.current, {
                    x: x,
                    y: y,
                    duration: 1,
                    ease: "power2.out",
                });
            };

            window.addEventListener('mousemove', handleMouseMove);
            return () => window.removeEventListener('mousemove', handleMouseMove);
        }, containerRef);

        return () => ctx.revert();
    }, []);

    return (
        <section ref={containerRef} className="relative h-screen flex items-center justify-center overflow-hidden">
            <div className="z-10 text-center" ref={textRef}>
                <h1 className="text-7xl md:text-9xl font-bold font-mono tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-500 mb-4">
                    RACEMATE
                </h1>
                <p className="text-xl md:text-2xl text-neon-blue font-light tracking-[0.5em] uppercase">
                    Real-Time Racing Intelligence
                </p>
            </div>

            {/* SVG Path for Car */}
            <svg className="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none" viewBox="0 0 1440 800">
                <path
                    id="hero-path"
                    d="M-100,400 C300,400 500,100 800,400 C1100,700 1300,400 1600,400"
                    fill="none"
                    stroke="url(#gradient)"
                    strokeWidth="2"
                />
                <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#00f3ff" stopOpacity="0" />
                        <stop offset="50%" stopColor="#00f3ff" stopOpacity="1" />
                        <stop offset="100%" stopColor="#00f3ff" stopOpacity="0" />
                    </linearGradient>
                </defs>
            </svg>

            {/* Car Icon */}
            <div ref={carRef} className="absolute top-0 left-0 w-12 h-24 bg-neon-red blur-[2px] opacity-80" style={{ clipPath: 'polygon(50% 0%, 100% 100%, 50% 85%, 0% 100%)' }}></div>

            <div className="absolute bottom-10 animate-bounce">
                <ArrowDown className="text-white/50 w-8 h-8" />
            </div>
        </section>
    );
};

export default Hero;

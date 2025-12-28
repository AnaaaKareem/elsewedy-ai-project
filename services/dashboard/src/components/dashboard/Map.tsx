'use client';

import React, { useEffect, useState } from 'react';
import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";
import { useTheme } from "next-themes";

import { LOCATIONS } from '@/lib/constants';

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface MapProps {
    onSelectCountry: (name: string | null) => void;
    selectedCountry: string | null;
}

export default function Map({ onSelectCountry, selectedCountry }: MapProps) {
    const { theme } = useTheme();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    const isDark = theme === 'dark';

    // Theme Configuration
    const styles = {
        defaultConfig: {
            fill: isDark ? "#2C2E33" : "#e2e8f0",
            stroke: isDark ? "#141517" : "#cbd5e1",
            strokeWidth: 0.5,
            outline: "none",
            transition: "all 0.3s"
        },
        hover: {
            fill: "#db2777", // Pink-600/700 equivalent or Primary
            opacity: 0.8,
            outline: "none",
            cursor: "pointer"
        },
        pressed: {
            fill: "#be185d",
            outline: "none"
        },
        selected: {
            fill: "#db2777",
            stroke: isDark ? "#141517" : "#cbd5e1",
            strokeWidth: 0.5,
            outline: "none"
        }
    };

    return (
        <div className="w-full h-full relative bg-muted/20 cursor-move transition-colors duration-300">
            <ComposableMap
                projection="geoMercator"
                projectionConfig={{
                    scale: 120,
                    center: [20, 10]
                }}
                className="w-full h-full"
            >
                <Geographies geography={GEO_URL}>
                    {({ geographies }) =>
                        geographies.map((geo) => {
                            const countryName = geo.properties.name.toUpperCase();
                            const isSelected = selectedCountry === countryName;
                            return (
                                <Geography
                                    key={geo.rsmKey}
                                    geography={geo}
                                    onClick={() => onSelectCountry(isSelected ? null : countryName)}
                                    style={{
                                        default: { fill: isSelected ? "#8b5cf6" : "#EAEAEC", stroke: "transparent", transition: "all 0.5s ease" },
                                        hover: { fill: "#8b5cf6", stroke: "transparent", transition: "all 0.3s ease", cursor: "pointer", filter: "drop-shadow(0px 0px 8px rgba(139, 92, 246, 0.6))" },
                                        pressed: { fill: "#7c3aed", stroke: "transparent" },
                                    }}
                                />
                            );
                        })
                    }
                </Geographies>

                {LOCATIONS.map(({ name, coordinates }) => {
                    const isSelected = selectedCountry === name;
                    return (
                        <Marker key={name} coordinates={coordinates as [number, number]}>
                            <circle r={6} fill="#8b5cf6" className="animate-pulse" stroke="#fff" strokeWidth={2} />
                            <circle r={12} fill="transparent" stroke="#8b5cf6" strokeWidth={1} strokeOpacity={0.5} className="animate-ping" />
                            {isSelected && (
                                <text
                                    textAnchor="middle"
                                    y={-10}
                                    style={{
                                        fontFamily: "inherit",
                                        fontSize: "12px",
                                        fill: isDark ? "white" : "#1e293b",
                                        fontWeight: "bold",
                                        textShadow: "0px 2px 4px rgba(0,0,0,0.5)"
                                    }}
                                    className="animate-fade-in"
                                >
                                    {name}
                                </text>
                            )}
                        </Marker>
                    );
                })}
            </ComposableMap>
        </div>
    );
}

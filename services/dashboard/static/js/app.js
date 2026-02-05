// ============================================================================
// SENTINEL DASHBOARD - Interactive Map & Market Intelligence
// ============================================================================

// --- APP STATE ---
const state = {
    selectedCountry: null,
    materials: [],
    shuffleIndex: 0,
    shufflePaused: false,
    shuffleInterval: null,
    markers: []
};

// --- CONFIGURATION ---
const SHUFFLE_INTERVAL_MS = 8000; // 8 seconds between country changes

// --- MAP INITIALIZATION ---
const map = L.map('map', {
    zoomControl: false,
    attributionControl: false
}).setView([20.0, 30.0], 2.5);

L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 20
}).addTo(map);

// Country Markers - EXACTLY matching codebase from shared/infrastructure/init_db.py
// 21 countries total
// 21 countries total
// 21 countries total
const countries = [
    // MENA
    { name: 'Egypt', coords: [26.82, 30.80], code: '818', iso3: 'EGY', region: 'MENA' },
    { name: 'UAE', coords: [23.42, 53.84], code: '784', iso3: 'ARE', region: 'MENA' },
    { name: 'Saudi Arabia', coords: [23.88, 45.07], code: '682', iso3: 'SAU', region: 'MENA' },
    // APAC
    { name: 'China', coords: [35.86, 104.19], code: '156', iso3: 'CHN', region: 'APAC' },
    { name: 'India', coords: [20.59, 78.96], code: '356', iso3: 'IND', region: 'APAC' },
    { name: 'Japan', coords: [36.20, 138.25], code: '392', iso3: 'JPN', region: 'APAC' },
    { name: 'S.Korea', coords: [35.90, 127.76], code: '410', iso3: 'KOR', region: 'APAC' },
    { name: 'Australia', coords: [-25.27, 133.77], code: '36', iso3: 'AUS', region: 'APAC' },
    // EU
    { name: 'Germany', coords: [51.16, 10.45], code: '276', iso3: 'DEU', region: 'EU' },
    { name: 'Italy', coords: [41.87, 12.56], code: '380', iso3: 'ITA', region: 'EU' },
    { name: 'France', coords: [46.22, 2.21], code: '251', iso3: 'FRA', region: 'EU' },
    { name: 'Spain', coords: [40.46, -3.74], code: '724', iso3: 'ESP', region: 'EU' },
    { name: 'UK', coords: [55.37, -3.43], code: '826', iso3: 'GBR', region: 'EU' },
    // NA
    { name: 'USA', coords: [37.09, -95.71], code: '842', iso3: 'USA', region: 'NA' },
    { name: 'Canada', coords: [56.13, -106.34], code: '124', iso3: 'CAN', region: 'NA' },
    // LATAM
    { name: 'Brazil', coords: [-14.23, -51.92], code: '76', iso3: 'BRA', region: 'LATAM' },
    { name: 'Mexico', coords: [23.63, -102.55], code: '484', iso3: 'MEX', region: 'LATAM' },
    { name: 'Argentina', coords: [-38.41, -63.61], code: '32', iso3: 'ARG', region: 'LATAM' },
    // SSA
    { name: 'South Africa', coords: [-30.55, 22.93], code: '710', iso3: 'ZAF', region: 'SSA' },
    { name: 'Nigeria', coords: [9.08, 8.67], code: '566', iso3: 'NGA', region: 'SSA' },
    { name: 'Kenya', coords: [-0.02, 37.90], code: '404', iso3: 'KEN', region: 'SSA' }
];

// Marker styling
const defaultMarkerStyle = {
    radius: 8,
    fillColor: '#dc2626',
    color: '#fff',
    weight: 1,
    opacity: 1,
    fillOpacity: 0.6
};

const activeMarkerStyle = {
    radius: 12,
    fillColor: '#ef4444',
    color: '#fff',
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
};

// Store GeoJSON layers
state.geoJsonLayers = {};

// Load World GeoJSON for Borders
async function loadGeoJson() {
    try {
        const response = await fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json');
        const data = await response.json();

        L.geoJSON(data, {
            filter: function (feature) {
                // Check if this country is in our list
                return countries.some(c => c.iso3 === feature.id);
            },
            style: {
                color: '#dc2626',
                weight: 1,
                opacity: 0, // Hidden by default
                fillColor: '#dc2626',
                fillOpacity: 0 // Hidden by default
            },
            onEachFeature: function (feature, layer) {
                // Store reference to layer by ISO3 code
                if (feature.id) {
                    state.geoJsonLayers[feature.id] = layer;
                }
            }
        }).addTo(map);

        console.log("GeoJSON borders loaded successfully");

    } catch (e) {
        console.error("Failed to load map borders:", e);
    }
}

// Add Markers to map
countries.forEach((c, index) => {
    const marker = L.circleMarker(c.coords, defaultMarkerStyle).addTo(map);
    state.markers.push(marker);

    // Click Event - pauses shuffle and selects country
    marker.on('click', () => {
        state.shufflePaused = true;
        selectCountry(c, index);
        // Resume after 20 seconds of inactivity
        setTimeout(() => {
            state.shufflePaused = false;
        }, 20000);
    });

    // Tooltip
    marker.bindTooltip(`${c.name} (${c.region})`, { permanent: false, direction: 'top' });
});

// --- AUTO-SHUFFLE FUNCTIONALITY ---

function startAutoShuffle() {
    console.log('Starting auto-shuffle...');

    // Load borders first
    loadGeoJson().then(() => {
        // Start immediately with first country
        selectCountry(countries[0], 0);

        state.shuffleInterval = setInterval(() => {
            if (!state.shufflePaused) {
                // Move to next country
                state.shuffleIndex = (state.shuffleIndex + 1) % countries.length;
                const country = countries[state.shuffleIndex];
                console.log(`Auto-shuffling to: ${country.name}`);
                selectCountry(country, state.shuffleIndex);
            }
        }, SHUFFLE_INTERVAL_MS);
    });
}

function updateShuffleIndicator(countryName) {
    const indicator = document.getElementById('shuffle-country');
    if (indicator) {
        indicator.textContent = countryName;
    }
}

// --- UI FUNCTIONS ---

function selectCountry(country, markerIndex) {
    state.selectedCountry = country;

    // Reset all markers to default style
    state.markers.forEach((m) => {
        m.setStyle(defaultMarkerStyle);
        m.setRadius(defaultMarkerStyle.radius);
    });

    // Highlight selected marker
    if (markerIndex !== undefined && state.markers[markerIndex]) {
        state.markers[markerIndex].setStyle(activeMarkerStyle);
        state.markers[markerIndex].setRadius(activeMarkerStyle.radius);
    }

    // UI Updates
    const placeholder = document.getElementById('country-placeholder');
    const infoPanel = document.getElementById('country-info');

    if (placeholder) placeholder.classList.add('hidden');
    if (infoPanel) infoPanel.classList.remove('hidden');

    const nameEl = document.getElementById('selected-country-name');
    if (nameEl) nameEl.textContent = country.name;

    updateShuffleIndicator(country.name);

    // Map Movement Logic: smart fitBounds if border exists, else flyTo
    if (state.geoJsonLayers && state.geoJsonLayers[country.iso3]) {
        const layer = state.geoJsonLayers[country.iso3];
        // Pad the bounds slightly so borders aren't touching screen edges
        map.flyToBounds(layer.getBounds(), {
            padding: [50, 50],
            duration: 1.5,
            maxZoom: 8 // Don't zoom in *too* close for tiny countries
        });

        // Reset all borders to invisible
        Object.values(state.geoJsonLayers).forEach(l => l.setStyle({ opacity: 0, fillOpacity: 0 }));

        // Highlight ONLY active country border
        layer.setStyle({
            color: '#dc2626',
            weight: 3,
            opacity: 1,     // Visible border
            fillOpacity: 0  // No fill
        });

    } else {
        // Fallback if GeoJSON failed or missing
        map.flyTo(country.coords, country.zoom || 5, { duration: 1.5 });
    }



    // Fetch Details from API
    fetchCountryDetails(country.code);

    // Refresh market feed immediately
    updateMarketFeed();
}

async function fetchCountryDetails(code) {
    try {
        const res = await fetch(`/api/country/${code}`);
        const data = await res.json();

        console.log(`Country data for ${code}:`, data);

        if (data.error) {
            setCountryMetrics('N/A', 'N/A', '0', 'Unknown');
            return;
        }

        setCountryMetrics(
            data.economic_health || 'Stable',
            typeof data.local_demand_index === 'number'
                ? data.local_demand_index.toFixed(1)
                : data.local_demand_index || '--',
            data.active_projects || 0,
            data.risk_level || 'Low'
        );

    } catch (err) {
        console.error("Failed to fetch country details:", err);
        setCountryMetrics('Error', '--', '--', '--');
    }
}

function setCountryMetrics(econHealth, demandIndex, activeProjects, riskLevel) {
    const setEl = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };

    setEl('econ-health', econHealth);
    setEl('demand-index', demandIndex);
    setEl('active-projects', activeProjects);
    setEl('risk-level', riskLevel);
}

async function updateMarketFeed() {
    try {
        const res = await fetch(`/api/live?t=${Date.now()}`);
        const data = await res.json();

        console.log('Market feed data:', data);

        const container = document.getElementById('material-list');
        if (!container) return;

        // Get materials from API response
        let items = data.materials || [];

        // Also include AI signals as materials if available
        if (data.ai_signals && data.ai_signals.length > 0) {
            data.ai_signals.forEach(signal => {
                const exists = items.some(m =>
                    (m.name || m.material) === signal.material
                );
                if (!exists) {
                    items.push({
                        name: signal.material,
                        price: signal.input_price,
                        decision: signal.decision,
                        trend: 0,
                        source: 'ai_signal'
                    });
                }
            });
        }

        // If still no data, show waiting message
        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="loading-spinner">
                    No live data available.<br>
                    <small style="color: #666;">Waiting for market feed...</small>
                </div>
            `;
            return;
        }

        container.innerHTML = ''; // Clear current

        items.forEach(mat => {
            const card = createMaterialCard(mat);
            container.appendChild(card);
        });

    } catch (err) {
        console.error("Feed Update Error:", err);
        const container = document.getElementById('material-list');
        if (container) {
            container.innerHTML = `
                <div class="loading-spinner">
                    Connection error.<br>
                    <small style="color: #666;">Retrying...</small>
                </div>
            `;
        }
    }
}

function createMaterialCard(mat) {
    const div = document.createElement('div');

    // Decision Mapping
    let decisionClass = 'wait';
    const decision = (mat.decision || '').toUpperCase();
    if (decision === 'BUY') decisionClass = 'buy';
    if (decision === 'HOLD') decisionClass = 'hold';

    // Trend Logic
    const trend = parseFloat(mat.trend) || 0;
    const isUp = trend >= 0;
    const trendClass = isUp ? 'trend-up' : 'trend-down';
    const trendArrow = isUp ? '▲' : '▼';

    // Price formatting
    const price = parseFloat(mat.price || mat.input_price) || 0;

    // Format price based on magnitude
    let priceStr;
    if (price >= 1000) {
        priceStr = `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else {
        priceStr = `$${price.toFixed(2)}`;
    }

    div.className = `material-card ${decisionClass}`;
    div.innerHTML = `
        <div class="card-top">
            <span class="mat-name">${mat.name || mat.material || 'Unknown'}</span>
            <span class="badge ${decisionClass}">${decision || 'WAIT'}</span>
        </div>
        <div class="card-bottom">
            <span class="mat-price">${priceStr}</span>
            <span class="${trendClass}">${trendArrow} ${Math.abs(trend).toFixed(2)}%</span>
        </div>
    `;
    return div;
}

// --- INITIALIZATION ---
console.log('Sentinel Dashboard initializing...');

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function init() {
    console.log('DOM ready, starting dashboard...');

    // Start market feed updates
    updateMarketFeed();
    setInterval(updateMarketFeed, 5000); // Poll every 5s

    // Start auto-shuffle
    startAutoShuffle();

    console.log('Dashboard initialized successfully.');
}

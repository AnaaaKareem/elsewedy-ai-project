
// --- APP STATE ---
const state = {
    selectedCountry: null,
    materials: []
};

// --- MAP INITIALIZATION ---
// Using Leaflet + CartoDB Dark Matter tiles (free)
const map = L.map('map', {
    zoomControl: false,
    attributionControl: false
}).setView([20.0, 30.0], 3); // Centered roughly on MENA/Global

L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 20
}).addTo(map);

// Country Markers (Lat/Lon approximation)
const countries = [
    // MENA
    { name: 'Egypt', coords: [26.82, 30.80], code: '818' },
    { name: 'UAE', coords: [23.42, 53.84], code: '784' },
    { name: 'Saudi Arabia', coords: [23.88, 45.07], code: '682' },
    // APAC
    { name: 'China', coords: [35.86, 104.19], code: '156' },
    { name: 'India', coords: [20.59, 78.96], code: '356' },
    { name: 'Japan', coords: [36.20, 138.25], code: '392' },
    { name: 'S.Korea', coords: [35.90, 127.76], code: '410' },
    { name: 'Australia', coords: [-25.27, 133.77], code: '36' },
    // EU
    { name: 'Germany', coords: [51.16, 10.45], code: '276' },
    { name: 'Italy', coords: [41.87, 12.56], code: '380' },
    { name: 'France', coords: [46.22, 2.21], code: '251' },
    { name: 'Spain', coords: [40.46, -3.74], code: '724' },
    { name: 'UK', coords: [55.37, -3.43], code: '826' },
    // NA
    { name: 'USA', coords: [37.09, -95.71], code: '842' },
    { name: 'Canada', coords: [56.13, -106.34], code: '124' },
    // LATAM
    { name: 'Brazil', coords: [-14.23, -51.92], code: '76' },
    { name: 'Mexico', coords: [23.63, -102.55], code: '484' },
    { name: 'Argentina', coords: [-38.41, -63.61], code: '32' },
    // SSA
    { name: 'South Africa', coords: [-30.55, 22.93], code: '710' },
    { name: 'Nigeria', coords: [9.08, 8.67], code: '566' },
    { name: 'Kenya', coords: [-0.02, 37.90], code: '404' }
];

// Add Markers
countries.forEach(c => {
    const marker = L.circleMarker(c.coords, {
        radius: 8,
        fillColor: '#00f2ea',
        color: '#fff',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.6
    }).addTo(map);

    // Click Event
    marker.on('click', () => {
        selectCountry(c);
        // Highlight effect
        map.flyTo(c.coords, 5, { duration: 1.5 });
    });

    // Tooltip
    marker.bindTooltip(c.name, { permanent: false, direction: 'top' });
});

// --- UI FUNCTIONS ---

function selectCountry(country) {
    state.selectedCountry = country;

    // UI Updates
    document.getElementById('country-placeholder').classList.add('hidden');
    const infoPanel = document.getElementById('country-info');
    infoPanel.classList.remove('hidden');

    document.getElementById('selected-country-name').textContent = country.name;

    // Fetch Details mock
    fetchCountryDetails(country.code);
}

async function fetchCountryDetails(code) {
    // Determine the API URL correctly. 
    // In production this might be a full URL, locally it is relative.
    try {
        const res = await fetch(`/api/country/\${code}`);
        const data = await res.json();

        document.getElementById('econ-health').textContent = data.economic_health;
        document.getElementById('demand-index').textContent = data.local_demand_index;
        document.getElementById('active-projects').textContent = data.active_projects;
        document.getElementById('risk-level').textContent = data.risk_level;

    } catch (err) {
        console.error("Failed to fetch country details", err);
    }
}

async function updateMarketFeed() {
    try {
        const res = await fetch('/api/live');
        const data = await res.json();

        const container = document.getElementById('material-list');

        // If no data, show mockup data for demonstration if empty
        let items = data.materials;

        // --- DEMO DATA INJECTION IF API EMPTY (FOR FIRST RUN VISUALS) ---
        if (!items || items.length === 0) {
            items = generateMockData();
        }

        container.innerHTML = ''; // Clear current

        items.forEach(mat => {
            const card = createMaterialCard(mat);
            container.appendChild(card);
        });

    } catch (err) {
        console.error("Feed Update Error", err);
    }
}

function createMaterialCard(mat) {
    const div = document.createElement('div');
    // Decision Mapping
    let decisionClass = 'wait';
    if (mat.decision === 'BUY') decisionClass = 'buy';
    if (mat.decision === 'HOLD') decisionClass = 'hold';

    // Trend Logic
    const isUp = mat.trend >= 0;
    const trendClass = isUp ? 'trend-up' : 'trend-down';
    const trendArrow = isUp ? '▲' : '▼';

    div.className = `material-card ${decisionClass}`;
    div.innerHTML = `
        <div class="card-top">
            <span class="mat-name">${mat.name || mat.material}</span>
            <span class="badge ${decisionClass}">${mat.decision || 'WAIT'}</span>
        </div>
        <div class="card-bottom">
            <span class="mat-price">$${Number(mat.price || mat.input_price).toFixed(2)}</span>
            <span class="${trendClass}">${trendArrow} ${Math.abs(mat.trend || 0.5).toFixed(2)}%</span>
        </div>
    `;
    return div;
}

// Mock Data Generator for verification when DB is empty
function generateMockData() {
    return [
        { name: 'Copper (LME)', price: 8540.50, trend: 1.2, decision: 'BUY' },
        { name: 'PVC Resin', price: 920.00, trend: -0.5, decision: 'WAIT' },
        { name: 'Aluminum', price: 2150.00, trend: 0.1, decision: 'HOLD' },
        { name: 'XLPE', price: 1100.25, trend: 2.5, decision: 'BUY' },
        { name: 'GSW Steel', price: 650.00, trend: -1.2, decision: 'WAIT' },
    ];
}

// --- INIT ---
updateMarketFeed();
setInterval(updateMarketFeed, 5000); // Poll every 5s

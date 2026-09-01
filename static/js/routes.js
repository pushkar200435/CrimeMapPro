
document.addEventListener('DOMContentLoaded', () => {
    // 1. Populate default date/time fields
    const today = new Date();
    const dateInput = document.getElementById('route-date');
    const timeInput = document.getElementById('route-time');
    
    if (dateInput) dateInput.value = today.toISOString().split('T')[0];
    if (timeInput) {
        const hours = String(today.getHours()).padStart(2, '0');
        const minutes = String(today.getMinutes()).padStart(2, '0');
        timeInput.value = `${hours}:${minutes}`;
    }

    // 2. Handle Routing Form Submit
    const routingForm = document.getElementById('routing-form');
    const mapFrame = document.getElementById('route-map-frame');
    const mapLoading = document.getElementById('map-loading');
    const routeDetailsCard = document.getElementById('route-details-card');
    const routeStatus = document.getElementById('route-status');

    if (routingForm) {
        routingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const source = document.getElementById('source').value;
            const destination = document.getElementById('destination').value;
            const date = dateInput.value;
            const time = timeInput.value;
            const modelType = document.getElementById('route-model').value;
            
            if (source === destination) {
                showToast("Source and destination cannot be the same district.", "error");
                return;
            }
            
            // Show loading overlays
            if (mapLoading) mapLoading.style.display = 'flex';
            if (routeDetailsCard) routeDetailsCard.style.display = 'none';
            routeStatus.textContent = 'Calculating path costs...';
            
            const payload = { source, destination, date, time, model_type: modelType };
            
            try {
                const response = await fetch('/api/route/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (!response.ok || data.error) {
                    showToast(data.error || 'Failed to calculate routing paths.', 'error');
                    if (mapLoading) mapLoading.style.display = 'none';
                    routeStatus.textContent = 'Calculation failed';
                    return;
                }
                
                // Success: update details comparison card
                const routes = data.routes;
                
                // Update SAFEST Path
                document.getElementById('safest-nodes').textContent = routes.safest.path.join(' → ');
                document.getElementById('safest-dist').textContent = `${routes.safest.distance} km`;
                document.getElementById('safest-time').textContent = `${routes.safest.time} mins`;
                document.getElementById('safest-score').textContent = `${routes.safest.safety_score}%`;
                
                // Update BALANCED Path
                document.getElementById('balanced-nodes').textContent = routes.balanced.path.join(' → ');
                document.getElementById('balanced-dist').textContent = `${routes.balanced.distance} km`;
                document.getElementById('balanced-time').textContent = `${routes.balanced.time} mins`;
                document.getElementById('balanced-score').textContent = `${routes.balanced.safety_score}%`;

                // Update SHORTEST Path
                document.getElementById('shortest-nodes').textContent = routes.shortest.path.join(' → ');
                document.getElementById('shortest-dist').textContent = `${routes.shortest.distance} km`;
                document.getElementById('shortest-time').textContent = `${routes.shortest.time} mins`;
                document.getElementById('shortest-score').textContent = `${routes.shortest.safety_score}%`;
                
                // Refresh Folium map iframe with route paths
                const mapUrl = `/map-route-raw?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}&date=${date}&time=${time}&model_type=${modelType}`;
                mapFrame.src = mapUrl;
                
                // Wait briefly for map to load then remove loading indicator
                mapFrame.onload = () => {
                    if (mapLoading) mapLoading.style.display = 'none';
                    if (routeDetailsCard) routeDetailsCard.style.display = 'block';
                    routeStatus.textContent = `Calculated: ${source} to ${destination}`;
                };
                
                showToast("Safe routing pathing overlays loaded successfully!", "success");
                
            } catch (err) {
                showToast("Error connecting to route prediction engine.", "error");
                if (mapLoading) mapLoading.style.display = 'none';
                routeStatus.textContent = 'Server connection failed';
            }
        });
    }
});

// 3. Location Safety Check Action
async function runSafetyCheck() {
    const location = document.getElementById('check-location').value;
    const dateInput = document.getElementById('route-date');
    const timeInput = document.getElementById('route-time');
    const modelType = document.getElementById('route-model') ? document.getElementById('route-model').value : 'rf';
    
    if (!location) {
        showToast("Please select a location to perform a safety check.", "error");
        return;
    }
    
    const date = dateInput ? dateInput.value : new Date().toISOString().split('T')[0];
    const time = timeInput ? timeInput.value : "12:00";
    
    const payload = { location, date, time, model_type: modelType };
    const outputCard = document.getElementById('check-output');
    
    try {
        const response = await fetch('/api/safety-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!response.ok || data.error) {
            showToast(data.error || 'Failed to complete safety assessment.', 'error');
            return;
        }
        
        // Populate safety check fields
        document.getElementById('check-title').textContent = location;
        
        const scoreEl = document.getElementById('check-score');
        scoreEl.textContent = `${data.safety_score}%`;
        
        const badge = document.getElementById('check-badge');
        badge.textContent = `${data.risk_level} Risk`;
        
        // Style badge colors
        if (data.risk_level === 'High') {
            badge.style.background = 'rgba(239, 68, 68, 0.15)';
            badge.style.border = '1px solid rgba(239, 68, 68, 0.3)';
            badge.style.color = '#f87171';
            scoreEl.style.color = '#f87171';
        } else if (data.risk_level === 'Medium') {
            badge.style.background = 'rgba(245, 158, 11, 0.15)';
            badge.style.border = '1px solid rgba(245, 158, 11, 0.3)';
            badge.style.color = '#fbbf24';
            scoreEl.style.color = '#fbbf24';
        } else {
            badge.style.background = 'rgba(16, 185, 129, 0.15)';
            badge.style.border = '1px solid rgba(16, 185, 129, 0.3)';
            badge.style.color = '#34d399';
            scoreEl.style.color = '#34d399';
        }
        
        // Add recommendations/tips
        const tipsContainer = document.getElementById('check-tips');
        tipsContainer.innerHTML = '<strong>Safety Tips:</strong><br/>';
        
        data.tips.forEach(tip => {
            tipsContainer.innerHTML += `<div style="margin-top: 4px; line-height: 1.4;">• ${tip}</div>`;
        });
        
        // Display output card
        outputCard.style.display = 'block';
        showToast(`Safety check completed for ${location}!`, "success");
        
    } catch (err) {
        showToast("Error calling safety check endpoint.", "error");
    }
}

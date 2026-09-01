
document.addEventListener('DOMContentLoaded', () => {
    // 1. Fetch data from embedded JSON script
    const dataElement = document.getElementById('chart-data');
    if (!dataElement) return;
    
    const summary = JSON.parse(dataElement.textContent);
    
    // Default shared fonts/colors
    const labelColor = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#94a3b8';
    const gridColor = 'rgba(148, 163, 184, 0.12)';
    
    // Set global Chart.js defaults
    Chart.defaults.color = labelColor;
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
    Chart.defaults.font.size = 12;

    // --- CHART 1: MONTHLY TRENDS (LINE) ---
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx && summary.monthly_trends && summary.monthly_trends.length > 0) {
        const months = summary.monthly_trends.map(t => t.month);
        const counts = summary.monthly_trends.map(t => t.count);

        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Crime Volume',
                    data: counts,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#22d3ee',
                    pointBorderColor: '#fff',
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: labelColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: labelColor, precision: 0 }
                    }
                }
            }
        });
    }

    // --- CHART 2: CATEGORY DISTRIBUTION (DOUGHNUT) ---
    const catCtx = document.getElementById('categoryChart');
    if (catCtx && summary.crime_types && summary.crime_types.length > 0) {
        const catLabels = summary.crime_types.map(c => c.name);
        const catValues = summary.crime_types.map(c => c.value);
        
        // Custom palette
        const colors = [
            '#6366f1', '#8b5cf6', '#3b82f6', '#06b6d4', 
            '#10b981', '#f59e0b', '#ef4444', '#ec4899'
        ];

        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    data: catValues,
                    backgroundColor: colors,
                    borderWidth: 1,
                    borderColor: 'rgba(255, 255, 255, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: labelColor,
                            boxWidth: 12,
                            padding: 15,
                            font: { size: 11 }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }

    // --- CHART 3: AREA-WISE STATISTICS (BAR) ---
    const areaCtx = document.getElementById('areaChart');
    if (areaCtx && summary.location_stats && summary.location_stats.length > 0) {
        const locLabels = summary.location_stats.map(l => l.name);
        const locValues = summary.location_stats.map(l => l.value);

        new Chart(areaCtx, {
            type: 'bar',
            data: {
                labels: locLabels,
                datasets: [{
                    label: 'Incidents Count',
                    data: locValues,
                    backgroundColor: 'rgba(34, 211, 238, 0.75)',
                    hoverBackgroundColor: '#22d3ee',
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: labelColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: labelColor }
                    }
                }
            }
        });
    }

    // --- DATASET CSV UPLOAD LOGIC ---
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const progressIndicator = document.getElementById('upload-progress');

    if (uploadZone && fileInput) {
        // Trigger click on file input
        uploadZone.addEventListener('click', () => fileInput.click());

        // Dragover styling
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--primary)';
            uploadZone.style.background = 'rgba(99, 102, 241, 0.08)';
        });

        // Reset styling on leave
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.style.borderColor = 'var(--border-color)';
            uploadZone.style.background = 'rgba(15, 23, 42, 0.2)';
        });

        // Drop file
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--border-color)';
            uploadZone.style.background = 'rgba(15, 23, 42, 0.2)';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });

        // Select file via dialog
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleFileUpload(fileInput.files[0]);
            }
        });
    }

    async function handleFileUpload(file) {
        if (!file.name.endsWith('.csv')) {
            showToast('Invalid file format. Please upload a CSV file.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // UI progress state
        uploadZone.style.display = 'none';
        progressIndicator.style.display = 'block';

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (result.success) {
                showToast(result.message, 'success');
                // Reload dashboard after brief delay to let toast display
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                showToast(result.error || 'Failed to process file.', 'error');
                progressIndicator.style.display = 'none';
                uploadZone.style.display = 'block';
            }
        } catch (err) {
            showToast('Server error during upload. Please check configurations.', 'error');
            progressIndicator.style.display = 'none';
            uploadZone.style.display = 'block';
        }
    }
});

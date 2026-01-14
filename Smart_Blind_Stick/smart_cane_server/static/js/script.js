// Global variables
let socket = null;
let distanceChart = null;
let chartData = {
    labels: [],
    datasets: [
        {
            label: 'Phía trước',
            data: [],
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            tension: 0.4
        },
        {
            label: 'Bên trái',
            data: [],
            borderColor: '#28a745',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            tension: 0.4
        },
        {
            label: 'Bên phải',
            data: [],
            borderColor: '#ffc107',
            backgroundColor: 'rgba(255, 193, 7, 0.1)',
            tension: 0.4
        }
    ]
};

// Initialize Socket.IO connection
function initSocket() {
    socket = io();

    socket.on('connect', function () {
        console.log('Connected to server');
        updateStatus('connected');
    });

    socket.on('sensor_update', function (data) {
        updateSensorDisplay(data);
        updateChart(data);
        updateHistory(data);
    });

    socket.on('alerts', function (alerts) {
        updateAlerts(alerts);
    });

    socket.on('disconnect', function () {
        console.log('Disconnected from server');
        updateStatus('disconnected');
    });
}

// Update sensor display
function updateSensorDisplay(data) {
    // Update distances
    document.getElementById('front-distance').textContent =
        data.front_distance === 0 ? '---' : data.front_distance.toFixed(1);
    document.getElementById('left-distance').textContent =
        data.left_distance === 0 ? '---' : data.left_distance.toFixed(1);
    document.getElementById('right-distance').textContent =
        data.right_distance === 0 ? '---' : data.right_distance.toFixed(1);
    document.getElementById('ir-distance').textContent =
        data.ir_distance === 0 ? '---' : data.ir_distance.toFixed(1);

    // Update progress bars
    updateProgressBar('front-progress', data.front_distance, 300);
    updateProgressBar('left-progress', data.left_distance, 300);
    updateProgressBar('right-progress', data.right_distance, 300);
    updateProgressBar('ir-progress', data.ir_distance, 80);

    // Update IR status
    let irStatus = document.getElementById('ir-status');
    if (data.ir_distance < 20) {
        irStatus.textContent = 'Trạng thái: Mặt đất không bằng phẳng';
        irStatus.className = 'text-danger mt-1';
    } else if (data.ir_distance > 40) {
        irStatus.textContent = 'Trạng thái: Có hố/bậc thềm';
        irStatus.className = 'text-warning mt-1';
    } else {
        irStatus.textContent = 'Trạng thái: Bình thường';
        irStatus.className = 'text-success mt-1';
    }

    // Update device status
    document.getElementById('device-mode').textContent =
        `Mode ${data.mode || 1}`;

    // Update power status
    const powerIcon = document.getElementById('power-icon');
    const powerStatus = document.getElementById('power-status');
    if (data.power_status) {
        powerIcon.className = 'bi bi-power text-success fs-4';
        powerStatus.textContent = 'Đang bật';
        powerStatus.className = 'fw-bold text-success';
    } else {
        powerIcon.className = 'bi bi-power text-danger fs-4';
        powerStatus.textContent = 'Đang tắt';
        powerStatus.className = 'fw-bold text-danger';
    }

    // Update time
    updateCurrentTime();
}

// Update progress bar
function updateProgressBar(elementId, value, max) {
    const progressBar = document.getElementById(elementId);
    if (!progressBar) return;

    let percentage = (value / max) * 100;
    if (percentage > 100) percentage = 100;

    progressBar.style.width = `${percentage}%`;

    // Change color based on value
    if (max === 80) { // IR sensor
        if (value < 20) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (value > 40) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    } else { // Distance sensors
        if (value < 25) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (value < 50) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    }
}

// Update alerts display
function updateAlerts(alerts) {
    const alertsList = document.getElementById('alerts-list');
    alertsList.innerHTML = '';

    if (alerts.length === 0) {
        alertsList.innerHTML = `
            <div class="list-group-item text-center text-muted py-4">
                <i class="bi bi-check-circle fs-1 text-success"></i>
                <p class="mt-2 mb-0">Không có cảnh báo</p>
            </div>
        `;
        return;
    }

    alerts.forEach(alert => {
        let icon = 'bi-exclamation-triangle';
        let color = 'warning';

        if (alert.severity === 'high') {
            icon = 'bi-exclamation-octagon';
            color = 'danger';
        } else if (alert.severity === 'low') {
            icon = 'bi-info-circle';
            color = 'info';
        }

        const alertElement = document.createElement('div');
        alertElement.className = `list-group-item list-group-item-action list-group-item-${color}`;
        alertElement.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <div>
                    <i class="bi ${icon} me-2"></i>
                    <strong>${alert.type === 'obstacle' ? 'Chướng ngại vật' :
                alert.type === 'hole' ? 'Hố' :
                    alert.type === 'ground' ? 'Mặt đất' : 'Cảnh báo'}</strong>
                </div>
                <small>${new Date().toLocaleTimeString()}</small>
            </div>
            <p class="mb-1">${alert.message}</p>
            <small>Vị trí: ${alert.location}</small>
        `;

        alertsList.appendChild(alertElement);
    });
}

// Update chart
function updateChart(data) {
    const now = new Date().toLocaleTimeString();

    // Add new data point
    chartData.labels.push(now);
    chartData.datasets[0].data.push(data.front_distance);
    chartData.datasets[1].data.push(data.left_distance);
    chartData.datasets[2].data.push(data.right_distance);

    // Keep only last 20 points
    if (chartData.labels.length > 20) {
        chartData.labels.shift();
        chartData.datasets.forEach(dataset => dataset.data.shift());
    }

    // Update chart
    if (distanceChart) {
        distanceChart.update();
    }
}

// Update history table
function updateHistory(data) {
    const table = document.getElementById('history-table');

    // Create new row
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td>${new Date().toLocaleTimeString()}</td>
        <td>${data.front_distance === 0 ? '---' : data.front_distance.toFixed(1)}</td>
        <td>${data.left_distance === 0 ? '---' : data.left_distance.toFixed(1)}</td>
        <td>${data.right_distance === 0 ? '---' : data.right_distance.toFixed(1)}</td>
    `;

    // Add to beginning of table
    table.insertBefore(newRow, table.firstChild);

    // Keep only last 10 rows
    while (table.children.length > 10) {
        table.removeChild(table.lastChild);
    }
}

// Initialize chart
function initChart() {
    const ctx = document.getElementById('distanceChart').getContext('2d');
    distanceChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Khoảng cách theo thời gian'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Khoảng cách (cm)'
                    }
                }
            }
        }
    });
}

// Update current time
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('vi-VN');
    const dateString = now.toLocaleDateString('vi-VN');
    document.getElementById('current-time').textContent =
        `${dateString} ${timeString}`;
}

// Update connection status
function updateStatus(status) {
    const statusElement = document.getElementById('wifi-status');
    const iconElement = document.getElementById('wifi-icon');

    if (status === 'connected') {
        statusElement.textContent = 'Đã kết nối';
        statusElement.className = 'fw-bold text-success';
        iconElement.className = 'bi bi-wifi text-success fs-4';
    } else {
        statusElement.textContent = 'Mất kết nối';
        statusElement.className = 'fw-bold text-danger';
        iconElement.className = 'bi bi-wifi-off text-danger fs-4';
    }
}

// Load historical data
async function loadHistoryData() {
    try {
        const response = await fetch('/api/data/history?hours=1');
        const data = await response.json();

        // Populate history table
        const table = document.getElementById('history-table');
        table.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            const time = new Date(item.timestamp);
            row.innerHTML = `
                <td>${time.toLocaleTimeString()}</td>
                <td>${item.front_distance === 0 ? '---' : item.front_distance.toFixed(1)}</td>
                <td>${item.left_distance === 0 ? '---' : item.left_distance.toFixed(1)}</td>
                <td>${item.right_distance === 0 ? '---' : item.right_distance.toFixed(1)}</td>
            `;
            table.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Event listeners
function setupEventListeners() {
    // Mode buttons
    document.querySelectorAll('[data-mode]').forEach(button => {
        button.addEventListener('click', function () {
            const mode = this.getAttribute('data-mode');

            // Update active state
            document.querySelectorAll('[data-mode]').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');

            // Send mode change to server
            fetch('/api/device/mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mode: parseInt(mode) })
            });
        });
    });

    // Save settings button
    document.getElementById('save-settings').addEventListener('click', function () {
        const dangerDist = document.getElementById('danger-dist').value;
        const warnDist = document.getElementById('warn-dist').value;
        const safeDist = document.getElementById('safe-dist').value;

        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                danger_distance: parseInt(dangerDist),
                warn_distance: parseInt(warnDist),
                safe_distance: parseInt(safeDist)
            })
        }).then(response => {
            if (response.ok) {
                alert('Cài đặt đã được lưu!');
            }
        });
    });
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function () {
    initSocket();
    initChart();
    loadHistoryData();
    setupEventListeners();

    // Update time every second
    setInterval(updateCurrentTime, 1000);

    // Load initial data
    fetch('/api/data/current')
        .then(response => response.json())
        .then(data => updateSensorDisplay(data))
        .catch(error => console.error('Error loading initial data:', error));
});
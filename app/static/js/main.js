// Main JavaScript functions for Crypto DeFi Analyzer

// Global variables
let isRefreshing = false;

// Utility functions
function formatNumber(num, decimals = 2) {
    if (!num || isNaN(num)) return 'N/A';
    
    const absNum = Math.abs(num);
    if (absNum >= 1e12) {
        return (num / 1e12).toFixed(decimals) + 'T';
    } else if (absNum >= 1e9) {
        return (num / 1e9).toFixed(decimals) + 'B';
    } else if (absNum >= 1e6) {
        return (num / 1e6).toFixed(decimals) + 'M';
    } else if (absNum >= 1e3) {
        return (num / 1e3).toFixed(decimals) + 'K';
    } else {
        return num.toFixed(decimals);
    }
}

function formatCurrency(num, currency = 'USD') {
    if (!num || isNaN(num)) return 'N/A';
    
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 6
    }).format(num);
}

function formatPercentage(num) {
    if (!num || isNaN(num)) return 'N/A';
    const sign = num >= 0 ? '+' : '';
    return sign + num.toFixed(2) + '%';
}

function formatDate(dateString, options = {}) {
    if (!dateString) return 'N/A';
    
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return new Date(dateString).toLocaleString('ru-RU', {...defaultOptions, ...options});
}

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    
    bsToast.show();
    
    // Remove toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    return container;
}

// Loading indicator
function showLoading(element, show = true) {
    if (show) {
        const spinner = document.createElement('div');
        spinner.className = 'text-center loading-indicator';
        spinner.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="mt-2 text-muted">Загрузка данных...</p>
        `;
        element.innerHTML = '';
        element.appendChild(spinner);
    } else {
        const loadingIndicator = element.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }
}

// Data refresh function
async function refreshData() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    const button = document.querySelector('[onclick="refreshData()"]');
    const originalText = button.innerHTML;
    
    try {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Обновление...';
        
        showToast('Начинаем обновление данных...', 'info');
        
        const response = await fetch('/api/data/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showToast('Данные успешно обновлены!', 'success');
            
            // Reload current page data if we're on a data page
            if (typeof loadCryptocurrencies === 'function') {
                loadCryptocurrencies();
            }
            if (typeof loadDeFiProtocols === 'function') {
                loadDeFiProtocols();
            }
            if (typeof loadAnalytics === 'function') {
                loadAnalytics();
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка обновления данных');
        }
        
    } catch (error) {
        console.error('Error refreshing data:', error);
        showToast('Ошибка при обновлении данных: ' + error.message, 'danger');
    } finally {
        button.disabled = false;
        button.innerHTML = originalText;
        isRefreshing = false;
    }
}

// API helper functions
async function apiGet(endpoint, params = {}) {
    const url = new URL(endpoint, window.location.origin);
    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
            url.searchParams.append(key, params[key]);
        }
    });
    
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function apiPost(endpoint, data = {}) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// Plotly chart helpers
function createBasicLineChart(container, data, title, xTitle = 'Дата', yTitle = 'Значение') {
    const layout = {
        title: title,
        xaxis: { 
            title: xTitle,
            type: 'date'
        },
        yaxis: { title: yTitle },
        margin: { t: 50, b: 50, l: 80, r: 50 },
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        font: { family: 'Segoe UI, sans-serif' }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };
    
    Plotly.newPlot(container, data, layout, config);
}

function createScatterPlot(container, xData, yData, title, xTitle, yTitle, colorData = null) {
    const trace = {
        x: xData,
        y: yData,
        mode: 'markers',
        type: 'scatter',
        marker: {
            size: 8,
            color: colorData || '#007bff',
            colorscale: 'Viridis',
            showscale: colorData ? true : false
        }
    };
    
    const layout = {
        title: title,
        xaxis: { title: xTitle },
        yaxis: { title: yTitle },
        margin: { t: 50, b: 50, l: 80, r: 50 }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };
    
    Plotly.newPlot(container, [trace], layout, config);
}

// Table helpers
function createDataTable(container, data, columns, options = {}) {
    const table = document.createElement('table');
    table.className = 'table table-hover table-striped';
    
    // Create header
    const thead = document.createElement('thead');
    thead.className = 'table-dark';
    const headerRow = document.createElement('tr');
    
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.title;
        if (col.sortable) {
            th.style.cursor = 'pointer';
            th.onclick = () => sortTable(table, col.key);
        }
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create body
    const tbody = document.createElement('tbody');
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        columns.forEach(col => {
            const td = document.createElement('td');
            let value = row[col.key];
            
            if (col.formatter) {
                value = col.formatter(value, row);
            }
            
            td.innerHTML = value;
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    container.innerHTML = '';
    container.appendChild(table);
}

// Sort table function
function sortTable(table, key) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.rows);
    
    const isNumeric = !isNaN(parseFloat(rows[0]?.cells[0]?.textContent));
    
    rows.sort((a, b) => {
        const aValue = a.cells[0].textContent;
        const bValue = b.cells[0].textContent;
        
        if (isNumeric) {
            return parseFloat(aValue) - parseFloat(bValue);
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+R for refresh
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            refreshData();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
    });
});

// Export functions for global use
window.CryptoAnalyzer = {
    formatNumber,
    formatCurrency,
    formatPercentage,
    formatDate,
    showToast,
    showLoading,
    refreshData,
    apiGet,
    apiPost,
    createBasicLineChart,
    createScatterPlot,
    createDataTable
};
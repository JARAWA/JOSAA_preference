// Add loading indicator
document.addEventListener('DOMContentLoaded', function() {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = 'Generating...';
            
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = '🔍 Generate Preferences';
            }, 5000);
        });
    }
});

// Add responsive table
function makeTableResponsive() {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-container';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseover', e => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = e.target.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = e.target.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
            tooltip.style.left = `${rect.left}px`;
        });
        
        element.addEventListener('mouseout', () => {
            document.querySelector('.tooltip').remove();
        });
    });
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    makeTableResponsive();
    initTooltips();
});

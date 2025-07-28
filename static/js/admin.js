// JavaScript específico para el panel de administración de LaIABot

document.addEventListener('DOMContentLoaded', function() {
    // Inicialización del admin
    initAdminPanel();
});

function initAdminPanel() {
    // Auto-hide flash messages después de 5 segundos
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 300);
        }, 5000);
    });

    // Confirmar eliminaciones
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || '¿Estás seguro de eliminar este elemento?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Sidebar móvil (si es necesario)
    handleMobileSidebar();
}

function handleMobileSidebar() {
    // En dispositivos móviles, el sidebar se colapsa automáticamente
    // Esta función se puede expandir para agregar funcionalidad de toggle
    
    if (window.innerWidth <= 768) {
        // Lógica para móviles si es necesaria
        console.log('Vista móvil detectada');
    }
}

// Funciones de utilidad para el admin
window.AdminUtils = {
    // Mostrar loader en tabla
    showTableLoader: function(tableContainer) {
        const loader = document.createElement('div');
        loader.className = 'table-loader';
        loader.innerHTML = `
            <div class="loader">
                <div class="spinner"></div>
                <div class="loader-text">Cargando...</div>
            </div>
        `;
        tableContainer.appendChild(loader);
        return loader;
    },

    // Remover loader
    removeTableLoader: function(loader) {
        if (loader && loader.parentNode) {
            loader.parentNode.removeChild(loader);
        }
    },

    // Formatear fecha para mostrar
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Truncar texto
    truncateText: function(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
};

// Manejo de redimensionamiento de ventana
window.addEventListener('resize', function() {
    handleMobileSidebar();
});

// Exportar para uso global
window.initAdminPanel = initAdminPanel;
// JavaScript principal para LaIABot
// Funcionalidades comunes para frontend y backend

// Utilidades globales
window.LaIABot = {
    // Configuración
    config: {
        apiUrl: window.location.origin,
        maxMessageLength: 1000,
        autoSaveDelay: 2000
    },
    
    // Funciones de utilidad
    utils: {
        // Formatear fecha
        formatDate: function(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays === 1) {
                return 'Ayer';
            } else if (diffDays < 7) {
                return `Hace ${diffDays} días`;
            } else {
                return date.toLocaleDateString('es-ES');
            }
        },
        
        // Formatear tiempo relativo
        formatTimeAgo: function(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffMinutes = Math.floor(diffTime / (1000 * 60));
            const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffMinutes < 1) {
                return 'Ahora';
            } else if (diffMinutes < 60) {
                return `Hace ${diffMinutes} min`;
            } else if (diffHours < 24) {
                return `Hace ${diffHours}h`;
            } else {
                return `Hace ${diffDays} días`;
            }
        },
        
        // Truncar texto
        truncateText: function(text, maxLength = 100) {
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        },
        
        // Escapar HTML
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
        
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Mostrar notificación toast
        showToast: function(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <span class="toast-icon">${this.getToastIcon(type)}</span>
                    <span class="toast-message">${message}</span>
                    <button class="toast-close">&times;</button>
                </div>
            `;
            
            // Agregar estilos si no existen
            if (!document.getElementById('toast-styles')) {
                const styles = document.createElement('style');
                styles.id = 'toast-styles';
                styles.textContent = `
                    .toast {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: white;
                        border-radius: var(--border-radius);
                        box-shadow: var(--shadow-lg);
                        z-index: 1000;
                        animation: slideInRight 0.3s ease-out;
                        max-width: 400px;
                        border-left: 4px solid;
                    }
                    
                    .toast-success { border-left-color: var(--success-color); }
                    .toast-error { border-left-color: var(--danger-color); }
                    .toast-warning { border-left-color: var(--warning-color); }
                    .toast-info { border-left-color: var(--accent-color); }
                    
                    .toast-content {
                        display: flex;
                        align-items: center;
                        padding: 1rem;
                        gap: 0.75rem;
                    }
                    
                    .toast-icon {
                        font-size: 1.25rem;
                        flex-shrink: 0;
                    }
                    
                    .toast-message {
                        flex: 1;
                        font-size: var(--font-size-sm);
                    }
                    
                    .toast-close {
                        background: none;
                        border: none;
                        font-size: 1.25rem;
                        cursor: pointer;
                        color: var(--medium-gray);
                        padding: 0;
                        line-height: 1;
                    }
                    
                    .toast-close:hover {
                        color: var(--text-color);
                    }
                    
                    @keyframes slideInRight {
                        from {
                            transform: translateX(100%);
                            opacity: 0;
                        }
                        to {
                            transform: translateX(0);
                            opacity: 1;
                        }
                    }
                    
                    @keyframes slideOutRight {
                        from {
                            transform: translateX(0);
                            opacity: 1;
                        }
                        to {
                            transform: translateX(100%);
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(styles);
            }
            
            document.body.appendChild(toast);
            
            // Auto-remove
            const autoRemove = setTimeout(() => {
                this.removeToast(toast);
            }, duration);
            
            // Manual close
            toast.querySelector('.toast-close').addEventListener('click', () => {
                clearTimeout(autoRemove);
                this.removeToast(toast);
            });
        },
        
        // Obtener icono del toast
        getToastIcon: function(type) {
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            return icons[type] || icons.info;
        },
        
        // Remover toast
        removeToast: function(toast) {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        },
        
        // Copiar al portapapeles
        copyToClipboard: function(text) {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text).then(() => {
                    this.showToast('Copiado al portapapeles', 'success');
                });
            } else {
                // Fallback para navegadores más antiguos
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    document.execCommand('copy');
                    this.showToast('Copiado al portapapeles', 'success');
                } catch (err) {
                    this.showToast('Error al copiar', 'error');
                }
                document.body.removeChild(textArea);
            }
        },
        
        // Validar formulario
        validateForm: function(formElement) {
            const inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('error');
                    isValid = false;
                } else {
                    input.classList.remove('error');
                }
            });
            
            return isValid;
        },
        
        // Hacer petición API
        apiRequest: async function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            const mergedOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                } else {
                    return await response.text();
                }
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        }
    },
    
    // Componentes reutilizables
    components: {
        // Crear modal
        createModal: function(options = {}) {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${options.title || 'Modal'}</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${options.content || ''}
                    </div>
                    ${options.showFooter !== false ? `
                    <div class="modal-footer">
                        <button class="btn btn-secondary modal-cancel">Cancelar</button>
                        <button class="btn btn-primary modal-confirm">${options.confirmText || 'Confirmar'}</button>
                    </div>
                    ` : ''}
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Event listeners
            const closeBtn = modal.querySelector('.modal-close');
            const cancelBtn = modal.querySelector('.modal-cancel');
            const confirmBtn = modal.querySelector('.modal-confirm');
            
            const closeModal = () => {
                modal.classList.remove('show');
                setTimeout(() => {
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }, 300);
            };
            
            if (closeBtn) closeBtn.addEventListener('click', closeModal);
            if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
            
            // Click outside to close
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
            
            // ESC to close
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    closeModal();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
            
            return {
                element: modal,
                show: () => modal.classList.add('show'),
                hide: closeModal,
                onConfirm: (callback) => {
                    if (confirmBtn) {
                        confirmBtn.addEventListener('click', callback);
                    }
                }
            };
        },
        
        // Crear loader
        createLoader: function(container, text = 'Cargando...') {
            const loader = document.createElement('div');
            loader.className = 'loader-container';
            loader.innerHTML = `
                <div class="loader">
                    <div class="spinner"></div>
                    <div class="loader-text">${text}</div>
                </div>
            `;
            
            container.appendChild(loader);
            return loader;
        },
        
        // Remover loader
        removeLoader: function(loader) {
            if (loader && loader.parentNode) {
                loader.parentNode.removeChild(loader);
            }
        }
    }
};

// Event listeners globales
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
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
    
    // Form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!LaIABot.utils.validateForm(form)) {
                e.preventDefault();
                LaIABot.utils.showToast('Por favor, completa todos los campos requeridos', 'error');
            }
        });
    });
    
    // Copy buttons
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.dataset.copy || this.textContent;
            LaIABot.utils.copyToClipboard(text);
        });
    });
    
    // Confirm buttons
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || '¿Estás seguro?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// Manejo de errores globales
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    LaIABot.utils.showToast('Ha ocurrido un error inesperado', 'error');
});

// Manejo de promesas rechazadas
window.addEventListener('unhandledrejection', function(e) {
    console.error('Promesa rechazada:', e.reason);
    LaIABot.utils.showToast('Error de conexión', 'error');
});

// Detectar cambios de conectividad
window.addEventListener('online', function() {
    LaIABot.utils.showToast('Conexión restaurada', 'success');
});

window.addEventListener('offline', function() {
    LaIABot.utils.showToast('Sin conexión a internet', 'warning');
});

// Exportar para uso global
window.showToast = LaIABot.utils.showToast.bind(LaIABot.utils);
window.apiRequest = LaIABot.utils.apiRequest.bind(LaIABot.utils);
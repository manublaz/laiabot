// Variables globales del chat
let currentThreadId = null;
let isLoading = false;
let conversations = [];
let messageCount = 0;
let autoExpandEnabled = true;
let lastScrollHeight = 0;

// Elementos del DOM
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const chatForm = document.getElementById('chat-form');
const sendBtn = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');
const conversationsList = document.getElementById('conversations-list');
const newChatBtn = document.getElementById('new-chat-btn');
const editTitleBtn = document.getElementById('edit-title-btn');
const deleteChatBtn = document.getElementById('delete-chat-btn');
const charCount = document.getElementById('char-count');
const conversationTitle = document.getElementById('conversation-title');
const chatMode = document.getElementById('chat-mode');
const chatContainer = document.querySelector('.chat-container');

// Modal elements
const editTitleModal = document.getElementById('edit-title-modal');
const modalClose = document.getElementById('modal-close');
const cancelEdit = document.getElementById('cancel-edit');
const saveTitle = document.getElementById('save-title');
const newTitleInput = document.getElementById('new-title-input');

// Configuración de auto-expansión
const AUTO_EXPAND_CONFIG = {
    minHeight: 15 * 16, // 15rem en px
    maxHeight: window.innerHeight * 0.85, // 85vh
    headerHeight: 5 * 16, // 5rem en px
    inputHeight: 7 * 16, // 7rem en px
    expandThreshold: 3, // Número de mensajes para empezar expansión
    expandIncrement: 4 * 16, // 4rem por mensaje nuevo
    smoothDuration: 400, // ms para animación
    debounceDelay: 150 // ms para debounce del resize
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadConversations();
    autoResizeTextarea();
    initializeAutoExpansion();
    
    // Initialize Feather Icons
    feather.replace();
    
    // Obtener thread ID de la URL o variable global
    const urlParams = new URLSearchParams(window.location.search);
    const threadFromUrl = urlParams.get('thread');
    
    if (threadFromUrl) {
        currentThreadId = parseInt(threadFromUrl);
    } else if (typeof window.currentThreadId !== 'undefined') {
        currentThreadId = window.currentThreadId;
    }
    
    if (currentThreadId) {
        highlightCurrentConversation();
        initializeMessageCount();
        adjustInitialChatHeight();
        scrollToBottom();
    }
});

// Inicialización de auto-expansión
function initializeAutoExpansion() {
    // Observer para detectar cambios en el contenido
    const messagesObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Solo procesar si se agregaron mensajes
                const addedMessages = Array.from(mutation.addedNodes).filter(node => 
                    node.nodeType === Node.ELEMENT_NODE && node.classList.contains('message')
                );
                
                if (addedMessages.length > 0) {
                    debounceAutoExpand();
                }
            }
        });
    });
    
    if (chatMessages) {
        messagesObserver.observe(chatMessages, {
            childList: true,
            subtree: false
        });
    }
    
    // Listener para cambios de ventana
    window.addEventListener('resize', debounceUpdateMaxHeight);
    
    // Configurar altura inicial
    updateMaxHeight();
}

// Inicializar contador de mensajes existentes
function initializeMessageCount() {
    const existingMessages = chatMessages.querySelectorAll('.message');
    messageCount = existingMessages.length;
    
    console.log(`Inicializando con ${messageCount} mensajes existentes`);
}

// Ajustar altura inicial del chat
function adjustInitialChatHeight() {
    if (!autoExpandEnabled || messageCount === 0) return;
    
    const contentHeight = chatMessages.scrollHeight;
    const viewportHeight = window.innerHeight;
    const maxAllowedHeight = viewportHeight * 0.85;
    const minRequiredHeight = AUTO_EXPAND_CONFIG.minHeight;
    
    // Calcular altura óptima
    let targetHeight = Math.max(contentHeight, minRequiredHeight);
    targetHeight = Math.min(targetHeight, maxAllowedHeight);
    
    // Solo expandir si tenemos suficientes mensajes
    if (messageCount >= AUTO_EXPAND_CONFIG.expandThreshold) {
        chatMessages.style.height = `${targetHeight}px`;
        chatMessages.classList.add('expanded');
        chatContainer.classList.add('expanded');
        
        console.log(`Altura inicial ajustada a ${targetHeight}px para ${messageCount} mensajes`);
    }
}

// Auto-expansión principal
function autoExpandChatMessages() {
    if (!autoExpandEnabled || !chatMessages) return;
    
    const currentScrollHeight = chatMessages.scrollHeight;
    const currentHeight = chatMessages.offsetHeight;
    const viewportHeight = window.innerHeight;
    const maxAllowedHeight = viewportHeight * 0.85 - AUTO_EXPAND_CONFIG.headerHeight - AUTO_EXPAND_CONFIG.inputHeight;
    
    // Solo expandir si el contenido excede la altura actual
    if (currentScrollHeight > currentHeight && currentHeight < maxAllowedHeight) {
        const newHeight = Math.min(currentScrollHeight + 20, maxAllowedHeight); // +20px padding
        
        // Aplicar transición suave
        chatMessages.classList.add('expanding');
        chatMessages.style.height = `${newHeight}px`;
        
        // Marcar como expandida
        if (newHeight > AUTO_EXPAND_CONFIG.minHeight) {
            chatMessages.classList.add('expanded');
            chatContainer.classList.add('expanded');
        }
        
        // Remover clase de transición después de la animación
        setTimeout(() => {
            chatMessages.classList.remove('expanding');
        }, AUTO_EXPAND_CONFIG.smoothDuration);
        
        console.log(`Chat expandido a ${newHeight}px (contenido: ${currentScrollHeight}px)`);
        
        // Scroll suave al final después de la expansión
        setTimeout(() => {
            scrollToBottomSmooth();
        }, AUTO_EXPAND_CONFIG.smoothDuration / 2);
    }
    
    // Gestionar indicador de scroll
    manageScrollIndicator();
}

// Gestionar indicador visual de scroll
function manageScrollIndicator() {
    if (!chatMessages) return;
    
    const hasOverflow = chatMessages.scrollHeight > chatMessages.offsetHeight;
    const isScrolledFromTop = chatMessages.scrollTop > 10;
    
    chatMessages.classList.toggle('has-overflow', hasOverflow);
    chatMessages.classList.toggle('scrollable', hasOverflow);
    chatMessages.classList.toggle('has-scroll', hasOverflow && isScrolledFromTop);
}

// Actualizar altura máxima basada en viewport
function updateMaxHeight() {
    const viewportHeight = window.innerHeight;
    const newMaxHeight = viewportHeight * 0.85 - AUTO_EXPAND_CONFIG.headerHeight - AUTO_EXPAND_CONFIG.inputHeight;
    
    document.documentElement.style.setProperty('--chat-max-height-dynamic', `${newMaxHeight}px`);
    
    // Ajustar altura actual si excede el nuevo máximo
    if (chatMessages && chatMessages.style.height) {
        const currentHeight = parseInt(chatMessages.style.height);
        if (currentHeight > newMaxHeight) {
            chatMessages.style.height = `${newMaxHeight}px`;
        }
    }
}

// Debounce para auto-expansión
const debounceAutoExpand = LaIABot.utils.debounce(autoExpandChatMessages, AUTO_EXPAND_CONFIG.debounceDelay);

// Debounce para actualización de altura máxima
const debounceUpdateMaxHeight = LaIABot.utils.debounce(updateMaxHeight, 250);

// Event Listeners
function setupEventListeners() {
    // Envío de mensajes
    chatForm.addEventListener('submit', handleSubmit);
    
    // Auto-resize del textarea
    messageInput.addEventListener('input', function() {
        autoResizeTextarea();
        updateCharCount();
    });
    
    // Enviar con Enter, nueva línea con Shift+Enter
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isLoading && messageInput.value.trim()) {
                handleSubmit(e);
            }
        }
    });
    
    // Botones de acción
    newChatBtn.addEventListener('click', createNewConversation);
    editTitleBtn.addEventListener('click', openEditTitleModal);
    deleteChatBtn.addEventListener('click', deleteCurrentConversation);
    
    // Modal
    modalClose.addEventListener('click', closeEditTitleModal);
    cancelEdit.addEventListener('click', closeEditTitleModal);
    saveTitle.addEventListener('click', saveConversationTitle);
    
    // Cerrar modal al hacer click fuera
    editTitleModal.addEventListener('click', function(e) {
        if (e.target === editTitleModal) {
            closeEditTitleModal();
        }
    });
    
    // Escape para cerrar modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && editTitleModal.classList.contains('show')) {
            closeEditTitleModal();
        }
    });
    
    // Listener para scroll en chat messages
    if (chatMessages) {
        chatMessages.addEventListener('scroll', handleChatScroll);
    }
}

// Manejar scroll del chat
function handleChatScroll() {
    manageScrollIndicator();
    
    // Auto-scroll inteligente: mantener en el fondo si el usuario estaba ahí
    const isNearBottom = chatMessages.scrollTop + chatMessages.offsetHeight >= chatMessages.scrollHeight - 50;
    chatMessages.classList.toggle('auto-scroll', isNearBottom);
}

// Manejo del envío de mensajes - MEJORADO PARA AUTO-EXPANSIÓN
async function handleSubmit(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    console.log('Enviando mensaje:', message);
    console.log('Thread ID actual:', currentThreadId);
    
    // Verificar que tenemos un thread ID válido
    if (!currentThreadId) {
        console.error('No hay thread ID disponible');
        LaIABot.utils.showToast('Error: No hay conversación activa', 'error');
        return;
    }
    
    // Deshabilitar input
    setLoading(true);
    
    // Añadir mensaje del usuario CON AUTO-EXPANSIÓN
    await addMessage(message, 'user', true);
    
    // Limpiar input
    messageInput.value = '';
    updateCharCount();
    autoResizeTextarea();
    
    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        console.log('Haciendo petición a /api/send_message...');
        
        // Enviar mensaje al servidor
        const response = await fetch('/api/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                thread_id: currentThreadId,
                message: message
            })
        });
        
        console.log('Respuesta recibida:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error en respuesta:', errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Datos recibidos:', data);
        
        // Ocultar indicador de escritura
        hideTypingIndicator();
        
        // Verificar que tenemos respuestas
        if (!data.responses || !Array.isArray(data.responses)) {
            console.error('Formato de respuesta inválido:', data);
            throw new Error('Formato de respuesta inválido');
        }
        
        // Actualizar modo si viene en la respuesta
        if (data.mode) {
            updateChatMode(data.mode);
        }
        
        // Añadir respuestas del bot CON AUTO-EXPANSIÓN
        if (data.responses.length > 0) {
            for (const response of data.responses) {
                console.log('Añadiendo respuesta del bot:', response.content.substring(0, 50) + '...');
                await addMessage(response.content, 'bot', true);
                await delay(300); // Pequeña pausa entre mensajes múltiples
            }
        } else {
            console.warn('No se recibieron respuestas del bot');
            await addMessage('No se recibió respuesta del servidor.', 'bot', true);
        }
        
        // Actualizar lista de conversaciones
        loadConversations();
        
    } catch (error) {
        console.error('Error completo:', error);
        hideTypingIndicator();
        
        // Mostrar error específico
        let errorMessage = 'Ha ocurrido un error inesperado.';
        
        if (error.message.includes('HTTP 500')) {
            errorMessage = 'Error interno del servidor. Revisa los logs.';
        } else if (error.message.includes('HTTP 400')) {
            errorMessage = 'Error en los datos enviados.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Error de conexión con el servidor.';
        }
        
        addMessage(errorMessage + ' (Detalles en consola)', 'bot', true);
        LaIABot.utils.showToast(errorMessage, 'error');
    } finally {
        setLoading(false);
    }
}

// Añadir mensaje al chat - MEJORADO CON AUTO-EXPANSIÓN
function addMessage(content, sender, animated = false, triggerExpansion = true) {
    return new Promise((resolve) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Añadir clase para nuevos mensajes animados
        if (animated) {
            messageDiv.classList.add('new-message');
        }
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        // Create SVG icon based on sender
        const svgIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svgIcon.setAttribute('data-feather', sender === 'user' ? 'user' : 'cpu');
        avatarDiv.appendChild(svgIcon);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        // Formatear contenido
        textDiv.innerHTML = formatMessageContent(content);
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        // Configurar animación inicial
        if (animated) {
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(20px) scale(0.95)';
        }
        
        // Añadir al DOM
        chatMessages.appendChild(messageDiv);
        
        // Initialize Feather icons for the new message
        feather.replace();
        
        // Incrementar contador de mensajes
        messageCount++;
        
        // Animación de entrada
        if (animated) {
            requestAnimationFrame(() => {
                messageDiv.style.transition = 'all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateY(0) scale(1)';
            });
        }
        
        // Trigger auto-expansión después de que el mensaje se haya renderizado
        if (triggerExpansion && sender === 'bot') {
            setTimeout(() => {
                debounceAutoExpand();
            }, animated ? 100 : 0);
        }
        
        // Scroll suave al final
        setTimeout(() => {
            scrollToBottomSmooth();
        }, animated ? 200 : 0);
        
        // Resolver promesa
        setTimeout(resolve, animated ? 500 : 0);
    });
}

// Scroll suave al final - MEJORADO
function scrollToBottomSmooth() {
    if (!chatMessages) return;
    
    const isNearBottom = chatMessages.scrollTop + chatMessages.offsetHeight >= chatMessages.scrollHeight - 100;
    
    // Solo hacer scroll automático si el usuario está cerca del final
    if (isNearBottom || chatMessages.classList.contains('auto-scroll')) {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// Scroll inmediato al final
function scrollToBottom() {
    if (!chatMessages) return;
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Formatear contenido del mensaje - MEJORADO PARA SOPORTAR HTML
function formatMessageContent(content) {
    // No escapar HTML si ya viene formateado (contiene etiquetas HTML)
    const hasHtmlTags = /<[^>]*>/.test(content);
    
    if (hasHtmlTags) {
        // Si ya contiene HTML (como las referencias APA con enlaces), renderizarlo directamente
        // Solo procesar saltos de línea adicionales
        return content.replace(/\n/g, '<br>');
    }
    
    // Para contenido sin HTML, aplicar el formato normal
    // Convertir URLs en enlaces
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    content = content.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Convertir saltos de línea
    content = content.replace(/\n/g, '<br>');
    
    // Resaltar texto en negrita
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    return content;
}

// Mostrar/ocultar indicador de escritura - MEJORADO
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
    
    // Pequeña pausa para que la expansión se active antes del scroll
    setTimeout(() => {
        debounceAutoExpand();
        scrollToBottomSmooth();
    }, 100);
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// Auto-resize del textarea
function autoResizeTextarea() {
    messageInput.style.height = '44px';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// Actualizar contador de caracteres
function updateCharCount() {
    const count = messageInput.value.length;
    charCount.textContent = count;
    
    if (count > 900) {
        charCount.style.color = 'var(--color-error)';
    } else if (count > 800) {
        charCount.style.color = 'var(--color-warning)';
    } else {
        charCount.style.color = 'var(--color-text-muted)';
    }
}

// Estado de carga
function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    messageInput.disabled = loading;
    
    if (loading) {
        sendBtn.innerHTML = `
            <div class="spinner"></div>
            <span class="btn-text">Enviando...</span>
        `;
    } else {
        sendBtn.innerHTML = `
            <svg class="btn-icon" data-feather="send"></svg>
            <span class="btn-text">Enviar</span>
        `;
        // Re-initialize Feather icons
        feather.replace();
    }
}

// Cargar lista de conversaciones
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        if (response.ok) {
            conversations = await response.json();
            renderConversations();
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

// Renderizar lista de conversaciones
function renderConversations() {
    conversationsList.innerHTML = '';
    
    if (conversations.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'conversation-item';
        emptyDiv.innerHTML = '<div class="conversation-title">No hay conversaciones</div>';
        conversationsList.appendChild(emptyDiv);
        return;
    }
    
    conversations.forEach(conversation => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'conversation-item';
        itemDiv.dataset.threadId = conversation.id;
        itemDiv.setAttribute('tabindex', '0');
        itemDiv.setAttribute('role', 'button');
        itemDiv.setAttribute('aria-label', `Conversación: ${conversation.title}`);
        
        if (conversation.id === currentThreadId) {
            itemDiv.classList.add('active');
        }
        
        const modeText = getModeText(conversation.mode);
        const date = new Date(conversation.date).toLocaleDateString('es-ES');
        
        itemDiv.innerHTML = `
            <div class="conversation-title">${conversation.title}</div>
            <div class="conversation-meta">
                <span>${modeText}</span>
                <span>${date}</span>
            </div>
        `;
        
        itemDiv.addEventListener('click', () => {
            loadConversation(conversation.id);
        });
        
        itemDiv.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                loadConversation(conversation.id);
            }
        });
        
        conversationsList.appendChild(itemDiv);
    });
}

// Obtener texto del modo
function getModeText(mode) {
    switch (mode) {
        case 1:
        case 'mode1':
            return 'Libros';
        case 2:
        case 'mode2':
            return 'Biblioteca';
        case 3:
        case 'mode3':
            return 'Chat';
        default:
            return 'Chat';
    }
}

// Cargar conversación
function loadConversation(threadId) {
    if (threadId === currentThreadId) return;
    
    window.location.href = `/chat/${threadId}`;
}

// Resaltar conversación actual
function highlightCurrentConversation() {
    const items = document.querySelectorAll('.conversation-item');
    items.forEach(item => {
        if (parseInt(item.dataset.threadId) === currentThreadId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Crear nueva conversación
async function createNewConversation() {
    try {
        // Redirigir a la ruta que crea nueva conversación
        window.location.href = '/new_chat';
    } catch (error) {
        console.error('Error creating new conversation:', error);
        LaIABot.utils.showToast('Error al crear nueva conversación', 'error');
    }
}

// Modal de editar título
function openEditTitleModal() {
    const currentTitle = conversationTitle.textContent;
    newTitleInput.value = currentTitle;
    editTitleModal.classList.add('show');
    newTitleInput.focus();
}

function closeEditTitleModal() {
    editTitleModal.classList.remove('show');
    newTitleInput.value = '';
}

// Guardar título de conversación
async function saveConversationTitle() {
    const newTitle = newTitleInput.value.trim();
    if (!newTitle) return;
    
    try {
        const response = await fetch('/api/update_conversation_title', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                thread_id: currentThreadId,
                title: newTitle
            })
        });
        
        if (response.ok) {
            conversationTitle.textContent = newTitle;
            loadConversations();
            closeEditTitleModal();
            LaIABot.utils.showToast('Título actualizado', 'success');
        }
    } catch (error) {
        console.error('Error updating title:', error);
        LaIABot.utils.showToast('Error al actualizar título', 'error');
    }
}

// Eliminar conversación actual
async function deleteCurrentConversation() {
    if (!currentThreadId) return;
    
    if (!confirm('¿Estás seguro de que quieres eliminar esta conversación? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/delete_conversation/${currentThreadId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            LaIABot.utils.showToast('Conversación eliminada', 'success');
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
        LaIABot.utils.showToast('Error al eliminar conversación', 'error');
    }
}

// Función de utilidad para delay
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Sidebar móvil
function toggleSidebar() {
    const sidebar = document.querySelector('.chat-sidebar');
    sidebar.classList.toggle('open');
}

// Detectar clics fuera del sidebar en móvil
document.addEventListener('click', function(e) {
    const sidebar = document.querySelector('.chat-sidebar');
    const isInsideSidebar = sidebar.contains(e.target);
    const isSidebarToggle = e.target.classList.contains('sidebar-toggle');
    
    if (!isInsideSidebar && !isSidebarToggle && window.innerWidth <= 768) {
        sidebar.classList.remove('open');
    }
});

// Responsive handling - MEJORADO PARA AUTO-EXPANSIÓN
function handleResize() {
    if (window.innerWidth > 768) {
        const sidebar = document.querySelector('.chat-sidebar');
        sidebar.classList.remove('open');
    }
    
    // Actualizar configuración de auto-expansión según el tamaño de pantalla
    updateAutoExpandConfig();
    updateMaxHeight();
}

// Actualizar configuración de auto-expansión según viewport
function updateAutoExpandConfig() {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    if (viewportWidth <= 480) {
        // Móvil pequeño
        AUTO_EXPAND_CONFIG.maxHeight = viewportHeight * 0.75;
        AUTO_EXPAND_CONFIG.headerHeight = 3.5 * 16;
        AUTO_EXPAND_CONFIG.inputHeight = 5 * 16;
        AUTO_EXPAND_CONFIG.minHeight = 10 * 16;
    } else if (viewportWidth <= 768) {
        // Tablet
        AUTO_EXPAND_CONFIG.maxHeight = viewportHeight * 0.80;
        AUTO_EXPAND_CONFIG.headerHeight = 4 * 16;
        AUTO_EXPAND_CONFIG.inputHeight = 6 * 16;
        AUTO_EXPAND_CONFIG.minHeight = 12 * 16;
    } else {
        // Desktop
        AUTO_EXPAND_CONFIG.maxHeight = viewportHeight * 0.85;
        AUTO_EXPAND_CONFIG.headerHeight = 5 * 16;
        AUTO_EXPAND_CONFIG.inputHeight = 7 * 16;
        AUTO_EXPAND_CONFIG.minHeight = 15 * 16;
    }
}

window.addEventListener('resize', LaIABot.utils.debounce(handleResize, 250));

// Actualizar modo de chat
function updateChatMode(mode) {
    const modeText = getModeText(mode);
    chatMode.textContent = `Modo: ${modeText}`;
    
    // Actualizar color según el modo
    chatMode.className = `chat-mode mode-${mode}`;
}

// Manejo de errores de red
window.addEventListener('online', function() {
    console.log('Conexión restaurada');
    LaIABot.utils.showToast('Conexión restaurada', 'success');
});

window.addEventListener('offline', function() {
    console.log('Sin conexión a internet');
    LaIABot.utils.showToast('Sin conexión a internet', 'warning');
});

// Accesibilidad - focus management
function manageFocus() {
    // Mantener el foco en el input cuando sea apropiado
    if (!isLoading && document.activeElement !== messageInput) {
        messageInput.focus();
    }
}

// Shortcuts de teclado - MEJORADOS
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter para nueva conversación
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        createNewConversation();
    }
    
    // Ctrl/Cmd + E para editar título
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        openEditTitleModal();
    }
    
    // Ctrl/Cmd + D para eliminar conversación
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        deleteCurrentConversation();
    }
    
    // Ctrl/Cmd + Shift + E para toggle auto-expansión
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'E') {
        e.preventDefault();
        toggleAutoExpansion();
    }
    
    // Page Down / Page Up para scroll en chat
    if (e.key === 'PageDown' && chatMessages.contains(document.activeElement)) {
        e.preventDefault();
        chatMessages.scrollBy(0, chatMessages.offsetHeight * 0.8);
    }
    
    if (e.key === 'PageUp' && chatMessages.contains(document.activeElement)) {
        e.preventDefault();
        chatMessages.scrollBy(0, -chatMessages.offsetHeight * 0.8);
    }
    
    // End para ir al final del chat
    if (e.key === 'End' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        scrollToBottomSmooth();
    }
    
    // Home para ir al inicio del chat
    if (e.key === 'Home' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        chatMessages.scrollTo({ top: 0, behavior: 'smooth' });
    }
});

// Toggle auto-expansión (para depuración o preferencia del usuario)
function toggleAutoExpansion() {
    autoExpandEnabled = !autoExpandEnabled;
    
    LaIABot.utils.showToast(
        `Auto-expansión ${autoExpandEnabled ? 'activada' : 'desactivada'}`, 
        'info'
    );
    
    // Guardar preferencia en localStorage si está disponible
    try {
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('laiabot_auto_expand', autoExpandEnabled.toString());
        }
    } catch (e) {
        console.log('localStorage no disponible');
    }
    
    console.log(`Auto-expansión ${autoExpandEnabled ? 'ACTIVADA' : 'DESACTIVADA'}`);
}

// Cargar preferencia de auto-expansión
function loadAutoExpandPreference() {
    try {
        if (typeof localStorage !== 'undefined') {
            const saved = localStorage.getItem('laiabot_auto_expand');
            if (saved !== null) {
                autoExpandEnabled = saved === 'true';
                console.log(`Preferencia de auto-expansión cargada: ${autoExpandEnabled}`);
            }
        }
    } catch (e) {
        console.log('No se pudo cargar preferencia de localStorage');
    }
}

// Funciones de utilidad para depuración
window.ChatDebug = {
    getMessageCount: () => messageCount,
    getAutoExpandEnabled: () => autoExpandEnabled,
    getChatHeight: () => chatMessages ? chatMessages.offsetHeight : 0,
    getChatScrollHeight: () => chatMessages ? chatMessages.scrollHeight : 0,
    getConfig: () => AUTO_EXPAND_CONFIG,
    toggleAutoExpand: toggleAutoExpansion,
    forceExpand: debounceAutoExpand,
    resetHeight: () => {
        if (chatMessages) {
            chatMessages.style.height = '';
            chatMessages.classList.remove('expanded');
            chatContainer.classList.remove('expanded');
        }
    }
};

// Inicialización de variables globales desde template
if (typeof window.currentThreadId !== 'undefined') {
    currentThreadId = window.currentThreadId;
}

// Cargar preferencias al inicializar
document.addEventListener('DOMContentLoaded', function() {
    loadAutoExpandPreference();
});

// Export para uso en otros scripts si es necesario
window.ChatApp = {
    loadConversation,
    createNewConversation,
    updateChatMode,
    addMessage,
    scrollToBottom,
    scrollToBottomSmooth,
    toggleAutoExpansion,
    autoExpandChatMessages: debounceAutoExpand
};
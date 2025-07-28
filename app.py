from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import yaml
import hashlib
import json
import requests
from datetime import datetime
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# Configuración
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

config = load_config()
app.secret_key = config['flask']['secret_key']

# Funciones auxiliares para base de datos
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def init_databases():
    """Inicializa las bases de datos con sus tablas"""
    
    # Base de datos del catálogo
    conn = get_db_connection('catalog.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS collection (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP,
        hash TEXT UNIQUE,
        permalink TEXT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        publisher TEXT,
        year INTEGER,
        abstract TEXT,
        tags TEXT,
        indexer TEXT
    )''')
    
    # Crear índice FTS5 para búsqueda de texto completo
    conn.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS collection_fts USING fts5(
        title, author, publisher, abstract, tags, indexer,
        content='collection', content_rowid='id'
    )''')
    conn.commit()
    conn.close()
    
    # Base de datos del chatbot
    conn = get_db_connection('chatbot.db')
    
    # Tabla de usuarios
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabla de prompts
    conn.execute('''CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP,
        mode TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )''')
    
    # Tabla de hilos de conversación
    conn.execute('''CREATE TABLE IF NOT EXISTS threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP,
        title TEXT DEFAULT 'Nueva conversación',
        mode INTEGER DEFAULT 1,
        status TEXT DEFAULT 'active'
    )''')
    
    # Tabla de comentarios
    conn.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER NOT NULL,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (thread_id) REFERENCES threads (id)
    )''')
    
    # Tabla de bienvenidas
    conn.execute('''CREATE TABLE IF NOT EXISTS welcome (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP,
        content TEXT NOT NULL
    )''')
    
    conn.commit()
    conn.close()
    
    # Base de datos de información de la biblioteca
    conn = get_db_connection('ourlibrary.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS infolib (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateregistry DATETIME DEFAULT CURRENT_TIMESTAMP,
        hash TEXT UNIQUE,
        permalink TEXT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        indexer TEXT
    )''')
    
    # Crear índice FTS5 para búsqueda de texto completo
    conn.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS infolib_fts USING fts5(
        title, content, indexer,
        content='infolib', content_rowid='id'
    )''')
    conn.commit()
    conn.close()

def create_admin_user():
    """Crea el usuario administrador por defecto"""
    conn = get_db_connection('chatbot.db')
    
    # Verificar si ya existe el usuario admin
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if not admin:
        password_hash = generate_password_hash('admin')
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    ('admin', password_hash))
        conn.commit()
    
    conn.close()

def get_random_welcome():
    """Obtiene un mensaje de bienvenida aleatorio"""
    conn = get_db_connection('chatbot.db')
    welcomes = conn.execute('SELECT content FROM welcome').fetchall()
    conn.close()
    
    if welcomes:
        return random.choice(welcomes)['content']
    else:
        return "¡Hola! Soy LaIABot, tu asistente bibliotecario. ¿En qué puedo ayudarte hoy?"

def call_groq_api(prompt, user_message):
    """Llama a la API de Groq con manejo mejorado de errores"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['groq']['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config['groq']['model'],
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": config['groq']['temperature'],
            "max_tokens": config['groq']['max_tokens']
        }
        
        print(f"Llamando a Groq API con modelo: {config['groq']['model']}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("Error 401: API Key inválida o expirada")
            return "Error: API Key inválida. Contacta al administrador."
        
        elif response.status_code == 429:
            print("Error 429: Límite de rate excedido")
            return "Error: Demasiadas consultas. Inténtalo en unos minutos."
        
        elif response.status_code == 400:
            print(f"Error 400: {response.text}")
            return "Error: Solicitud inválida. Verifica la configuración."
        
        response.raise_for_status()
        
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"Respuesta inesperada: {result}")
            return "Error: Respuesta inesperada de la API."
        
    except requests.exceptions.Timeout:
        print("Error: Timeout en la conexión")
        return "Error: La solicitud tardó demasiado. Inténtalo de nuevo."
    
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar a Groq")
        return "Error: No se pudo conectar al servicio de IA. Verifica tu conexión a internet."
    
    except requests.exceptions.RequestException as e:
        print(f"Error de requests: {e}")
        return f"Error de conexión: {str(e)}"
    
    except Exception as e:
        print(f"Error inesperado: {e}")
        return "Lo siento, hay un problema técnico. Inténtalo de nuevo."

def get_prompt(mode, type_prompt, status="active"):
    """Obtiene un prompt de la base de datos"""
    conn = get_db_connection('chatbot.db')
    prompt = conn.execute(
        'SELECT content FROM prompts WHERE mode = ? AND type = ? AND status = ?',
        (mode, type_prompt, status)
    ).fetchone()
    conn.close()
    
    if prompt:
        return prompt['content']
    else:
        return ""

def fallback_response(user_message, mode="mode3"):
    """Respuesta de fallback cuando la API no está disponible"""
    responses = {
        "mode1": {
            "user_response": "Disculpa, el servicio de recomendaciones está temporalmente no disponible. Mientras tanto, puedes explorar nuestro catálogo o contáctanos directamente para ayudarte a encontrar el libro perfecto.",
            "system_keywords": []
        },
        "mode2": {
            "user_response": "El servicio de información está temporalmente no disponible. Para consultas urgentes sobre horarios y servicios, puedes contactarnos directamente o consultar nuestro sitio web.",
            "system_keywords": ["servicio", "horario", "información"]
        },
        "mode3": "Disculpa, el servicio de chat está temporalmente no disponible. Puedes explorar nuestro catálogo de libros o consultar información sobre nuestros servicios en las otras secciones."
    }
    
    if mode in ["mode1", "mode2"]:
        return json.dumps(responses[mode])
    else:
        return responses["mode3"]

def determine_mode(user_message):
    """Determina el modo de funcionamiento basado en la intención del usuario"""
    intent_prompt = get_prompt("intent", "evaluation")
    if not intent_prompt:
        return "mode3"  # Default a conversación normal
    
    response = call_groq_api(intent_prompt, user_message)
    
    # Si hay error en la API, usar heurística simple
    if "Error:" in response:
        # Heurística básica para determinar modo sin API
        user_lower = user_message.lower()
        
        # Palabras clave para modo 1 (libros)
        book_keywords = ['libro', 'libros', 'leer', 'lectura', 'recomienda', 'recomendación', 
                        'autor', 'novela', 'poesía', 'ensayo', 'literatura', 'busco']
        
        # Palabras clave para modo 2 (biblioteca)
        library_keywords = ['horario', 'servicio', 'biblioteca', 'préstamo', 'renovar', 
                           'carnet', 'actividad', 'taller', 'evento', 'conferencia']
        
        if any(keyword in user_lower for keyword in book_keywords):
            return "mode1"
        elif any(keyword in user_lower for keyword in library_keywords):
            return "mode2"
        else:
            return "mode3"
    
    # Parsear la respuesta normal de la API
    if "mode1" in response.lower() or "modo1" in response.lower():
        return "mode1"
    elif "mode2" in response.lower() or "modo2" in response.lower():
        return "mode2"
    else:
        return "mode3"

def search_catalog(keywords):
    """Busca en el catálogo usando FTS5 y LIKE como fallback"""
    conn = get_db_connection('catalog.db')
    results = []
    
    if keywords:
        # Primero intentar con FTS5
        try:
            query = ' OR '.join(keywords) if isinstance(keywords, list) else keywords
            cursor = conn.execute(
                '''SELECT c.* FROM collection c 
                   JOIN collection_fts fts ON c.id = fts.rowid 
                   WHERE collection_fts MATCH ? 
                   ORDER BY rank LIMIT 5''', 
                (query,)
            )
            results = cursor.fetchall()
        except:
            pass
        
        # Si no hay resultados, usar LIKE
        if not results:
            search_term = ' '.join(keywords) if isinstance(keywords, list) else keywords
            cursor = conn.execute(
                '''SELECT * FROM collection 
                   WHERE indexer LIKE ? 
                   ORDER BY dateregistry DESC LIMIT 5''',
                (f'%{search_term}%',)
            )
            results = cursor.fetchall()
    
    conn.close()
    return results

def search_library_info(keywords):
    """Busca información de la biblioteca usando FTS5 y LIKE como fallback"""
    conn = get_db_connection('ourlibrary.db')
    results = []
    
    if keywords:
        # Primero intentar con FTS5
        try:
            query = ' OR '.join(keywords) if isinstance(keywords, list) else keywords
            cursor = conn.execute(
                '''SELECT i.* FROM infolib i 
                   JOIN infolib_fts fts ON i.id = fts.rowid 
                   WHERE infolib_fts MATCH ? 
                   ORDER BY rank LIMIT 5''', 
                (query,)
            )
            results = cursor.fetchall()
        except:
            pass
        
        # Si no hay resultados, usar LIKE
        if not results:
            search_term = ' '.join(keywords) if isinstance(keywords, list) else keywords
            cursor = conn.execute(
                '''SELECT * FROM infolib 
                   WHERE indexer LIKE ? 
                   ORDER BY dateregistry DESC LIMIT 5''',
                (f'%{search_term}%',)
            )
            results = cursor.fetchall()
    
    conn.close()
    return results

def format_apa_reference(book):
    """Formatea una referencia bibliográfica en formato APA con enlaces HTML"""
    year = f"({book['year']})" if book['year'] else "(s.f.)"
    publisher = f"{book['publisher']}" if book['publisher'] else "Editorial no especificada"
    
    # Enlaces HTML para el título y ficha
    permalink_url = book['permalink'] if book['permalink'] else f"/catalog/{book['hash']}"
    book_detail_url = url_for('book_detail', book_id=book['id'])
    
    # Formato APA con enlaces HTML - CORREGIDO
    title_link = f'<a href="{permalink_url}" target="_blank" rel="noopener noreferrer" class="book-title-link"><strong>{book["title"]}</strong></a>'
    detail_link = f'<a href="{book_detail_url}" target="_blank" rel="noopener noreferrer" class="book-detail-link">[ver ficha]</a>'
    
    return f"{book['author']} {year}. {title_link} {detail_link}. {publisher}."

def get_conversation_history(thread_id):
    """Obtiene el historial de conversación de un hilo"""
    conn = get_db_connection('chatbot.db')
    comments = conn.execute(
        'SELECT * FROM comments WHERE thread_id = ? ORDER BY dateregistry',
        (thread_id,)
    ).fetchall()
    conn.close()
    
    history = []
    for comment in comments:
        history.append({
            'sender': comment['sender'],
            'content': comment['content'],
            'timestamp': comment['dateregistry']
        })
    
    return history

def save_comment(thread_id, sender, content):
    """Guarda un comentario en la base de datos"""
    conn = get_db_connection('chatbot.db')
    conn.execute(
        'INSERT INTO comments (thread_id, sender, content) VALUES (?, ?, ?)',
        (thread_id, sender, content)
    )
    conn.commit()
    conn.close()

def extract_keywords_from_context(user_message):
    """Extrae palabras clave del mensaje del usuario como fallback"""
    # Palabras clave comunes para búsqueda
    message_lower = user_message.lower()
    
    # Palabras clave para libros
    book_keywords = ['libro', 'libros', 'novela', 'autor', 'ciencia ficción', 'sci-fi', 
                    'fantasy', 'fantasía', 'romance', 'misterio', 'terror', 'horror',
                    'biografía', 'historia', 'ensayo', 'poesía', 'drama', 'comedia',
                    'aventura', 'distopía', 'utopía', 'orwell', 'asimov', 'garcía márquez',
                    'borges', 'cortázar', 'vargas llosa', 'clásico', 'contemporáneo',
                    'realismo mágico', 'literatura', 'ficción', 'no ficción']
    
    # Palabras clave para biblioteca
    library_keywords = ['horario', 'servicio', 'biblioteca', 'préstamo', 'renovar',
                       'carnet', 'actividad', 'taller', 'evento', 'conferencia',
                       'wifi', 'wifi', 'impresión', 'fotocopia', 'sala', 'consulta']
    
    found_keywords = []
    
    # Buscar keywords en el mensaje
    for keyword in book_keywords + library_keywords:
        if keyword in message_lower:
            found_keywords.append(keyword)
    
    # Si no encuentra keywords específicas, usar palabras del mensaje
    if not found_keywords:
        words = message_lower.split()
        # Filtrar palabras cortas y comunes
        stop_words = ['de', 'la', 'el', 'en', 'y', 'a', 'que', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'sobre', 'algo', 'todo', 'esto', 'tengo', 'quiero', 'busco']
        found_keywords = [word for word in words if len(word) > 3 and word not in stop_words][:5]
    
    return found_keywords[:5]  # Máximo 5 keywords

def generate_basic_book_suggestions(books):
    """Genera sugerencias básicas de libros sin IA"""
    suggestions = []
    
    for book in books:
        # Crear referencia APA con enlaces HTML
        apa_ref = format_apa_reference(book)
        
        # Crear comentario básico basado en los datos del libro
        comment = f"→ {book['abstract'][:150]}..." if book['abstract'] else "→ Una excelente adición a tu biblioteca personal."
        
        suggestions.append(f"{apa_ref}\n{comment}")
    
    return "\n\n".join(suggestions)

def generate_hash(content):
    """Genera hash MD5"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# Decorador para requerir autenticación de administrador
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# RUTAS FRONTEND
@app.route('/')
def index():
    """Página principal - Chat directo"""
    # Verificar si hay una conversación activa en la sesión
    thread_id = session.get('current_thread_id')
    
    if thread_id:
        # Verificar que el hilo existe en la base de datos
        conn = get_db_connection('chatbot.db')
        existing_thread = conn.execute('SELECT * FROM threads WHERE id = ?', (thread_id,)).fetchone()
        conn.close()
        
        if existing_thread:
            # Cargar conversación existente
            history = get_conversation_history(thread_id)
            return render_template('chat.html', thread_id=thread_id, history=history)
    
    # Si no hay conversación activa, crear una nueva
    conn = get_db_connection('chatbot.db')
    cursor = conn.execute('INSERT INTO threads (title, mode) VALUES (?, ?)', 
                         ('Nueva conversación', 1))
    thread_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Guardar en la sesión
    session['current_thread_id'] = thread_id
    
    # Obtener mensaje de bienvenida
    welcome_message = get_random_welcome()
    save_comment(thread_id, 'bot', welcome_message)
    
    return render_template('chat.html', thread_id=thread_id, welcome_message=welcome_message)

@app.route('/new_chat')
def new_chat():
    """Crear nueva conversación explícitamente"""
    # Limpiar sesión actual
    session.pop('current_thread_id', None)
    
    # Crear nuevo hilo
    conn = get_db_connection('chatbot.db')
    cursor = conn.execute('INSERT INTO threads (title, mode) VALUES (?, ?)', 
                         ('Nueva conversación', 1))
    thread_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Guardar en la sesión
    session['current_thread_id'] = thread_id
    
    # Obtener mensaje de bienvenida
    welcome_message = get_random_welcome()
    save_comment(thread_id, 'bot', welcome_message)
    
    return redirect(url_for('chat', thread_id=thread_id))

@app.route('/chat/<int:thread_id>')
def chat(thread_id):
    """Cargar conversación existente"""
    history = get_conversation_history(thread_id)
    return render_template('chat.html', thread_id=thread_id, history=history)

# NUEVAS RUTAS PARA LIBROS
@app.route('/catalog/<book_hash>')
def book_permalink(book_hash):
    """Mostrar libro por su hash/permalink"""
    conn = get_db_connection('catalog.db')
    book = conn.execute('SELECT * FROM collection WHERE hash = ?', (book_hash,)).fetchone()
    conn.close()
    
    if not book:
        flash('Libro no encontrado', 'error')
        return redirect(url_for('index'))
    
    return render_template('book_permalink.html', book=book)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    """Mostrar ficha completa del libro"""
    conn = get_db_connection('catalog.db')
    book = conn.execute('SELECT * FROM collection WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    
    if not book:
        flash('Libro no encontrado', 'error')
        return redirect(url_for('index'))
    
    return render_template('book_detail.html', book=book)

@app.route('/api/send_message', methods=['POST'])
def send_message():
    """Procesa mensajes del usuario - VERSIÓN MEJORADA"""
    try:
        data = request.json
        thread_id = data.get('thread_id')
        user_message = data.get('message')
        
        print(f"Recibido mensaje: thread_id={thread_id}, message='{user_message[:50]}...'")
        
        if not thread_id or not user_message:
            print("Error: Datos incompletos")
            return jsonify({'error': 'Datos incompletos'}), 400
        
        # Guardar mensaje del usuario
        save_comment(thread_id, 'user', user_message)
        print("Mensaje del usuario guardado")
        
        # Determinar modo de funcionamiento
        mode = determine_mode(user_message)
        print(f"Modo determinado: {mode}")
        
        # Actualizar modo del hilo
        conn = get_db_connection('chatbot.db')
        conn.execute('UPDATE threads SET mode = ? WHERE id = ?', 
                    (mode, thread_id))
        conn.commit()
        conn.close()
        
        responses = []
        
        if mode == "mode1":
            print("Procesando modo 1 - Recomendaciones de libros")
            # Modo 1: Recomendaciones de libros
            base_prompt = get_prompt("mode1", "base")
            if base_prompt:
                print("Prompt encontrado, llamando a Groq...")
                response = call_groq_api(base_prompt, user_message)
                print(f"Respuesta de Groq: {response[:200]}...")
            else:
                print("No se encontró prompt, usando fallback")
                response = fallback_response(user_message, "mode1")
            
            # Si hay error de API, usar fallback
            if "Error:" in response:
                print("Error en API, usando fallback")
                response = fallback_response(user_message, "mode1")
            
            # Intentar parsear respuesta JSON
            user_response = ""
            keywords = []
            
            try:
                # Buscar JSON en la respuesta
                import re
                json_match = re.search(r'\{[^{}]*"user_response"[^{}]*"system_keywords"[^{}]*\}', response)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_response = json.loads(json_str)
                    user_response = parsed_response.get('user_response', response)
                    keywords = parsed_response.get('system_keywords', [])
                    print(f"JSON extraído correctamente. Keywords: {keywords}")
                else:
                    # Si no hay JSON, usar toda la respuesta como user_response
                    user_response = response
                    # Intentar extraer keywords del contexto
                    keywords = extract_keywords_from_context(user_message)
                    print(f"No se encontró JSON, keywords extraídas del contexto: {keywords}")
                    
            except Exception as e:
                print(f"Error parseando JSON: {e}")
                user_response = response
                keywords = extract_keywords_from_context(user_message)
                print(f"Usando keywords del contexto: {keywords}")
            
            # Añadir respuesta del usuario
            responses.append({
                'sender': 'bot',
                'content': user_response
            })
            
            # VALIDACIÓN MEJORADA: Solo buscar libros si hay keywords válidas
            if keywords and len(keywords) > 0:
                # Filtrar keywords vacías o muy cortas
                valid_keywords = [k.strip() for k in keywords if k.strip() and len(k.strip()) > 2]
                
                if valid_keywords:
                    print(f"Buscando libros con keywords válidas: {valid_keywords}")
                    books = search_catalog(valid_keywords)
                    print(f"Encontrados {len(books)} libros")
                    
                    if books:
                        # Crear referencias APA CON ENLACES HTML
                        book_references = []
                        for book in books:
                            book_references.append(format_apa_reference(book))
                        
                        books_text = "\n".join(book_references)
                        print(f"Referencias APA con enlaces creadas: {len(book_references)}")
                        
                        # Obtener comentarios de la IA para cada libro
                        suggest_prompt = get_prompt("mode1", "suggest")
                        if suggest_prompt:
                            print("Generando comentarios con IA...")
                            suggestion_response = call_groq_api(suggest_prompt, books_text)
                            
                            if "Error:" in suggestion_response:
                                print("Error en IA para comentarios, usando formato básico")
                                suggestion_response = generate_basic_book_suggestions(books)
                        else:
                            print("No hay prompt de sugerencias, usando formato básico")
                            suggestion_response = generate_basic_book_suggestions(books)
                        
                        # Añadir la segunda respuesta con recomendaciones
                        responses.append({
                            'sender': 'bot',
                            'content': f"📚 **Creemos que te puede interesar:**\n\n{suggestion_response}"
                        })
                        print("Segunda respuesta con libros añadida")
                    else:
                        print("No se encontraron libros, añadiendo mensaje informativo")
                        responses.append({
                            'sender': 'bot',
                            'content': "No encontré libros específicos para esas palabras clave en nuestro catálogo actual, pero puedo ayudarte a buscar con otros términos. ¿Podrías ser más específico sobre qué tipo de libro buscas?"
                        })
                else:
                    print("No hay keywords válidas suficientes para búsqueda")
            else:
                print("No hay keywords, continuando sin búsqueda de libros")
        
        elif mode == "mode2":
            print("Procesando modo 2 - Información de biblioteca")
            # Modo 2: Información de la biblioteca - Lógica similar a mode1
            base_prompt = get_prompt("mode2", "base")
            if base_prompt:
                response = call_groq_api(base_prompt, user_message)
            else:
                response = fallback_response(user_message, "mode2")
            
            # Si hay error de API, usar fallback
            if "Error:" in response:
                response = fallback_response(user_message, "mode2")
            
            # Intentar parsear respuesta JSON
            user_response = ""
            keywords = []
            
            try:
                import re
                json_match = re.search(r'\{[^{}]*"user_response"[^{}]*"system_keywords"[^{}]*\}', response)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_response = json.loads(json_str)
                    user_response = parsed_response.get('user_response', response)
                    keywords = parsed_response.get('system_keywords', [])
                else:
                    user_response = response
                    keywords = extract_keywords_from_context(user_message)
            except:
                user_response = response
                keywords = extract_keywords_from_context(user_message)
            
            responses.append({
                'sender': 'bot',
                'content': user_response
            })
            
            # Buscar información si hay palabras clave válidas
            if keywords and len(keywords) > 0:
                valid_keywords = [k.strip() for k in keywords if k.strip() and len(k.strip()) > 2]
                
                if valid_keywords:
                    print(f"Buscando información de biblioteca con keywords: {valid_keywords}")
                    info = search_library_info(valid_keywords)
                    print(f"Encontrados {len(info)} elementos de información")
                    
                    if info:
                        suggest_prompt = get_prompt("mode2", "suggest")
                        info_content = []
                        
                        for item in info:
                            info_content.append(f"**{item['title']}**\n{item['content']}")
                        
                        info_text = "\n\n".join(info_content)
                        
                        if suggest_prompt:
                            info_response = call_groq_api(suggest_prompt, info_text)
                            
                            if "Error:" in info_response:
                                info_response = f"🏛️ **Información de nuestra biblioteca:**\n\n{info_text}"
                        else:
                            info_response = f"🏛️ **Información de nuestra biblioteca:**\n\n{info_text}"
                        
                        responses.append({
                            'sender': 'bot',
                            'content': info_response
                        })
        
        else:
            print("Procesando modo 3 - Conversación normal")
            # Modo 3: Conversación normal
            limits_prompt = get_prompt("limits", "base")
            if limits_prompt:
                history = get_conversation_history(thread_id)
                
                # Construir contexto de conversación
                context = ""
                for msg in history[-10:]:  # Últimos 10 mensajes para contexto
                    context += f"{msg['sender']}: {msg['content']}\n"
                
                full_prompt = f"{limits_prompt}\n\nContexto de conversación:\n{context}\n\nUsuario: {user_message}"
                response = call_groq_api(full_prompt, "")
                
                # Si hay error de API, usar fallback
                if "Error:" in response:
                    response = fallback_response(user_message, "mode3")
            else:
                response = fallback_response(user_message, "mode3")
            
            responses.append({
                'sender': 'bot',
                'content': response
            })
        
        # Guardar respuestas del bot
        print(f"Guardando {len(responses)} respuestas del bot")
        for response in responses:
            save_comment(thread_id, response['sender'], response['content'])
        
        print("Proceso completado exitosamente")
        # IMPORTANTE: Enviar también el modo determinado al frontend
        return jsonify({
            'responses': responses,
            'mode': mode
        })
        
    except Exception as e:
        print(f"ERROR CRÍTICO en send_message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/api/conversations')
def get_conversations():
    """Obtiene lista de conversaciones"""
    conn = get_db_connection('chatbot.db')
    threads = conn.execute(
        'SELECT * FROM threads ORDER BY dateregistry DESC'
    ).fetchall()
    conn.close()
    
    conversations = []
    for thread in threads:
        conversations.append({
            'id': thread['id'],
            'title': thread['title'],
            'date': thread['dateregistry'],
            'mode': thread['mode']
        })
    
    return jsonify(conversations)

@app.route('/api/delete_conversation/<int:thread_id>', methods=['DELETE'])
def delete_conversation(thread_id):
    """Elimina una conversación"""
    conn = get_db_connection('chatbot.db')
    
    # Eliminar comentarios
    conn.execute('DELETE FROM comments WHERE thread_id = ?', (thread_id,))
    # Eliminar hilo
    conn.execute('DELETE FROM threads WHERE id = ?', (thread_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_conversation_title', methods=['POST'])
def update_conversation_title():
    """Actualiza el título de una conversación"""
    data = request.json
    thread_id = data.get('thread_id')
    new_title = data.get('title')
    
    if not thread_id or not new_title:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    conn = get_db_connection('chatbot.db')
    conn.execute('UPDATE threads SET title = ? WHERE id = ?', (new_title, thread_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# RUTAS BACKEND - Autenticación
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login del administrador"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection('chatbot.db')
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['admin'] = True
            session['user_id'] = user['id']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciales incorrectas')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout del administrador"""
    session.clear()
    return redirect(url_for('index'))

# RUTAS BACKEND - Panel de administración
@app.route('/admin')
@require_admin
def admin_dashboard():
    """Panel principal de administración"""
    return render_template('admin/dashboard.html')

@app.route('/admin/catalog')
@require_admin
def admin_catalog():
    """Gestión del catálogo"""
    conn = get_db_connection('catalog.db')
    books = conn.execute('SELECT * FROM collection ORDER BY dateregistry DESC').fetchall()
    conn.close()
    
    return render_template('admin/catalog.html', books=books)

@app.route('/admin/library_info')
@require_admin
def admin_library_info():
    """Gestión de información de la biblioteca"""
    conn = get_db_connection('ourlibrary.db')
    info = conn.execute('SELECT * FROM infolib ORDER BY dateregistry DESC').fetchall()
    conn.close()
    
    return render_template('admin/library_info.html', info=info)

@app.route('/admin/conversations')
@require_admin
def admin_conversations():
    """Gestión de conversaciones"""
    conn = get_db_connection('chatbot.db')
    threads = conn.execute(
        '''SELECT t.*, COUNT(c.id) as message_count 
           FROM threads t 
           LEFT JOIN comments c ON t.id = c.thread_id 
           GROUP BY t.id 
           ORDER BY t.dateregistry DESC'''
    ).fetchall()
    conn.close()
    
    return render_template('admin/conversations.html', threads=threads)

@app.route('/admin/prompts')
@require_admin
def admin_prompts():
    """Gestión de prompts"""
    conn = get_db_connection('chatbot.db')
    prompts = conn.execute('SELECT * FROM prompts ORDER BY mode, type').fetchall()
    conn.close()
    
    return render_template('admin/prompts.html', prompts=prompts)

@app.route('/admin/welcome')
@require_admin  
def admin_welcome():
    """Gestión de mensajes de bienvenida"""
    conn = get_db_connection('chatbot.db')
    welcomes = conn.execute('SELECT * FROM welcome ORDER BY dateregistry DESC').fetchall()
    conn.close()
    
    return render_template('admin/welcome.html', welcomes=welcomes)

@app.route('/admin/config')
@require_admin
def admin_config():
    """Configuración del sistema"""
    return render_template('admin/config.html', config=config)

# APIs del dashboard
@app.route('/admin/api/stats')
@require_admin
def admin_api_stats():
    """API para estadísticas del dashboard"""
    try:
        # Obtener estadísticas
        conn_catalog = get_db_connection('catalog.db')
        books_count = conn_catalog.execute('SELECT COUNT(*) as count FROM collection').fetchone()['count']
        conn_catalog.close()
        
        conn_library = get_db_connection('ourlibrary.db')
        library_info_count = conn_library.execute('SELECT COUNT(*) as count FROM infolib').fetchone()['count']
        conn_library.close()
        
        conn_chatbot = get_db_connection('chatbot.db')
        conversations_count = conn_chatbot.execute('SELECT COUNT(*) as count FROM threads').fetchone()['count']
        prompts_count = conn_chatbot.execute('SELECT COUNT(*) as count FROM prompts').fetchone()['count']
        conn_chatbot.close()
        
        return jsonify({
            'books': books_count,
            'library_info': library_info_count,
            'conversations': conversations_count,
            'prompts': prompts_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/recent-activity')
@require_admin
def admin_api_recent_activity():
    """API para actividad reciente"""
    try:
        conn = get_db_connection('chatbot.db')
        recent_threads = conn.execute(
            'SELECT * FROM threads ORDER BY dateregistry DESC LIMIT 5'
        ).fetchall()
        conn.close()
        
        activities = []
        for thread in recent_threads:
            activities.append({
                'description': f"Nueva conversación: {thread['title']}",
                'time': thread['dateregistry']
            })
        
        return jsonify(activities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/check-groq')
@require_admin
def admin_api_check_groq():
    """API para verificar estado de Groq"""
    try:
        # Hacer una prueba simple con la API
        response = call_groq_api("Responde solo 'OK'", "test")
        if "OK" in response or len(response) < 50:
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'status': 'error'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/api/check-fts')
@require_admin
def admin_api_check_fts():
    """API para verificar estado de índices FTS"""
    try:
        # Verificar FTS en catálogo
        conn = get_db_connection('catalog.db')
        conn.execute("SELECT * FROM collection_fts LIMIT 1")
        conn.close()
        
        # Verificar FTS en biblioteca
        conn = get_db_connection('ourlibrary.db')
        conn.execute("SELECT * FROM infolib_fts LIMIT 1")
        conn.close()
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# CRUD Operations para el backend

@app.route('/admin/catalog/add', methods=['GET', 'POST'])
@require_admin
def admin_add_book():
    """Agregar libro al catálogo"""
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        publisher = request.form.get('publisher', '')
        year = request.form.get('year', '')
        abstract = request.form.get('abstract', '')
        tags = request.form.get('tags', '')
        
        # Crear indexer
        indexer = f"{title} {author} {publisher} {abstract} {tags}"
        
        # Crear hash
        hash_content = f"{title}{author}{year}"
        book_hash = generate_hash(hash_content)
        
        # Crear permalink
        permalink = f"/catalog/{book_hash}"
        
        conn = get_db_connection('catalog.db')
        try:
            conn.execute('''
                INSERT INTO collection (hash, permalink, title, author, publisher, year, abstract, tags, indexer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (book_hash, permalink, title, author, publisher, year, abstract, tags, indexer))
            
            # Actualizar FTS
            try:
                conn.execute('INSERT INTO collection_fts(collection_fts) VALUES("rebuild")')
            except:
                pass
            conn.commit()
            flash('Libro agregado exitosamente', 'success')
        except sqlite3.IntegrityError:
            flash('Error: El libro ya existe', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('admin_catalog'))
    
    return render_template('admin/add_book.html')

@app.route('/admin/catalog/edit/<int:book_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_book(book_id):
    """Editar libro del catálogo"""
    conn = get_db_connection('catalog.db')
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        publisher = request.form.get('publisher', '')
        year = request.form.get('year', '')
        abstract = request.form.get('abstract', '')
        tags = request.form.get('tags', '')
        
        # Actualizar indexer
        indexer = f"{title} {author} {publisher} {abstract} {tags}"
        
        conn.execute('''
            UPDATE collection 
            SET title=?, author=?, publisher=?, year=?, abstract=?, tags=?, indexer=?
            WHERE id=?
        ''', (title, author, publisher, year, abstract, tags, indexer, book_id))
        
        # Actualizar FTS
        try:
            conn.execute('INSERT INTO collection_fts(collection_fts) VALUES("rebuild")')
        except:
            pass
        conn.commit()
        conn.close()
        
        flash('Libro actualizado exitosamente', 'success')
        return redirect(url_for('admin_catalog'))
    
    book = conn.execute('SELECT * FROM collection WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    
    if not book:
        flash('Libro no encontrado', 'error')
        return redirect(url_for('admin_catalog'))
    
    return render_template('admin/edit_book.html', book=book)

@app.route('/admin/catalog/delete/<int:book_id>', methods=['POST'])
@require_admin
def admin_delete_book(book_id):
    """Eliminar libro del catálogo"""
    conn = get_db_connection('catalog.db')
    conn.execute('DELETE FROM collection WHERE id = ?', (book_id,))
    try:
        conn.execute('INSERT INTO collection_fts(collection_fts) VALUES("rebuild")')
    except:
        pass
    conn.commit()
    conn.close()
    
    flash('Libro eliminado exitosamente', 'success')
    return redirect(url_for('admin_catalog'))

@app.route('/admin/library_info/add', methods=['GET', 'POST'])
@require_admin
def admin_add_library_info():
    """Agregar información de biblioteca"""
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Crear indexer
        indexer = f"{title} {content}"
        
        # Crear hash
        hash_content = f"{title}"
        info_hash = generate_hash(hash_content)
        
        # Crear permalink
        permalink = f"/library/{info_hash}"
        
        conn = get_db_connection('ourlibrary.db')
        try:
            conn.execute('''
                INSERT INTO infolib (hash, permalink, title, content, indexer)
                VALUES (?, ?, ?, ?, ?)
            ''', (info_hash, permalink, title, content, indexer))
            
            # Actualizar FTS
            try:
                conn.execute('INSERT INTO infolib_fts(infolib_fts) VALUES("rebuild")')
            except:
                pass
            conn.commit()
            flash('Información agregada exitosamente', 'success')
        except sqlite3.IntegrityError:
            flash('Error: La información ya existe', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('admin_library_info'))
    
    return render_template('admin/add_library_info.html')

@app.route('/admin/library_info/edit/<int:info_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_library_info(info_id):
    """Editar información de biblioteca"""
    conn = get_db_connection('ourlibrary.db')
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Actualizar indexer
        indexer = f"{title} {content}"
        
        conn.execute('''
            UPDATE infolib 
            SET title=?, content=?, indexer=?
            WHERE id=?
        ''', (title, content, indexer, info_id))
        
        # Actualizar FTS
        try:
            conn.execute('INSERT INTO infolib_fts(infolib_fts) VALUES("rebuild")')
        except:
            pass
        conn.commit()
        conn.close()
        
        flash('Información actualizada exitosamente', 'success')
        return redirect(url_for('admin_library_info'))
    
    info = conn.execute('SELECT * FROM infolib WHERE id = ?', (info_id,)).fetchone()
    conn.close()
    
    if not info:
        flash('Información no encontrada', 'error')
        return redirect(url_for('admin_library_info'))
    
    return render_template('admin/edit_library_info.html', info=info)

@app.route('/admin/library_info/delete/<int:info_id>', methods=['POST'])
@require_admin
def admin_delete_library_info(info_id):
    """Eliminar información de biblioteca"""
    conn = get_db_connection('ourlibrary.db')
    conn.execute('DELETE FROM infolib WHERE id = ?', (info_id,))
    try:
        conn.execute('INSERT INTO infolib_fts(infolib_fts) VALUES("rebuild")')
    except:
        pass
    conn.commit()
    conn.close()
    
    flash('Información eliminada exitosamente', 'success')
    return redirect(url_for('admin_library_info'))

@app.route('/admin/conversations/view/<int:thread_id>')
@require_admin
def admin_view_conversation(thread_id):
    """Ver detalles de una conversación"""
    conn = get_db_connection('chatbot.db')
    
    thread = conn.execute('SELECT * FROM threads WHERE id = ?', (thread_id,)).fetchone()
    comments = conn.execute(
        'SELECT * FROM comments WHERE thread_id = ? ORDER BY dateregistry',
        (thread_id,)
    ).fetchall()
    
    conn.close()
    
    if not thread:
        flash('Conversación no encontrada', 'error')
        return redirect(url_for('admin_conversations'))
    
    return render_template('admin/view_conversation.html', thread=thread, comments=comments)

@app.route('/admin/conversations/delete/<int:thread_id>', methods=['POST'])
@require_admin
def admin_delete_conversation(thread_id):
    """Eliminar conversación completa"""
    conn = get_db_connection('chatbot.db')
    
    # Eliminar comentarios
    conn.execute('DELETE FROM comments WHERE thread_id = ?', (thread_id,))
    # Eliminar hilo
    conn.execute('DELETE FROM threads WHERE id = ?', (thread_id,))
    
    conn.commit()
    conn.close()
    
    flash('Conversación eliminada exitosamente', 'success')
    return redirect(url_for('admin_conversations'))


@app.route('/admin/prompts/edit/<int:prompt_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_prompt(prompt_id):
    """Editar prompt del sistema"""
    conn = get_db_connection('chatbot.db')
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        status = request.form['status']
        
        conn.execute('''
            UPDATE prompts 
            SET title=?, content=?, status=?
            WHERE id=?
        ''', (title, content, status, prompt_id))
        
        conn.commit()
        conn.close()
        
        flash('Prompt actualizado exitosamente', 'success')
        return redirect(url_for('admin_prompts'))
    
    prompt = conn.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,)).fetchone()
    conn.close()
    
    if not prompt:
        flash('Prompt no encontrado', 'error')
        return redirect(url_for('admin_prompts'))
    
    return render_template('admin/edit_prompt.html', prompt=prompt)

@app.route('/admin/prompts/add', methods=['GET', 'POST'])
@require_admin
def admin_add_prompt():
    """Agregar nuevo prompt"""
    if request.method == 'POST':
        mode = request.form['mode']
        type_prompt = request.form['type']
        status = request.form['status']
        title = request.form['title']
        content = request.form['content']
        
        conn = get_db_connection('chatbot.db')
        try:
            conn.execute('''
                INSERT INTO prompts (mode, type, status, title, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (mode, type_prompt, status, title, content))
            conn.commit()
            flash('Prompt agregado exitosamente', 'success')
        except sqlite3.IntegrityError:
            flash('Error: Ya existe un prompt con esas características', 'error')
        finally:
            conn.close()
            
        return redirect(url_for('admin_prompts'))
    
    return render_template('admin/add_prompt.html')

@app.route('/admin/prompts/delete/<int:prompt_id>', methods=['POST'])
@require_admin
def admin_delete_prompt(prompt_id):
    """Eliminar prompt del sistema"""
    conn = get_db_connection('chatbot.db')
    conn.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
    conn.commit()
    conn.close()
    
    flash('Prompt eliminado exitosamente', 'success')
    return redirect(url_for('admin_prompts'))

if __name__ == '__main__':
    # Inicializar bases de datos
    init_databases()
    create_admin_user()
    
    app.run(debug=config['flask']['debug'], 
            host=config['flask']['host'], 
            port=config['flask']['port'])
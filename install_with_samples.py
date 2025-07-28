#!/usr/bin/env python3
"""
Script para cargar datos de ejemplo en las bases de datos de LaIABot
"""

import sqlite3
import hashlib
import json
from datetime import datetime

def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def init_databases():
    """Inicializa las bases de datos con sus tablas"""
    print("Inicializando bases de datos...")
    
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
    
    print("✓ Bases de datos inicializadas correctamente")

def create_admin_user():
    """Crea el usuario administrador por defecto"""
    print("Creando usuario administrador...")
    
    # Importar werkzeug para hash de contraseñas
    try:
        from werkzeug.security import generate_password_hash
    except ImportError:
        print("⚠️ Werkzeug no está instalado. Instalando...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "werkzeug"])
        from werkzeug.security import generate_password_hash
    
    conn = get_db_connection('chatbot.db')
    
    # Verificar si ya existe el usuario admin
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    
    if not admin:
        password_hash = generate_password_hash('admin')
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    ('admin', password_hash))
        conn.commit()
        print("✓ Usuario administrador creado: admin/admin")
    else:
        print("✓ Usuario administrador ya existe")
    
    conn.close()

def generate_hash(text):
    """Genera un hash MD5 para el texto"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def load_catalog_data():
    """Carga libros de ejemplo en el catálogo"""
    print("Cargando libros de ejemplo...")
    
    books = [
        {
            "title": "Cien años de soledad",
            "author": "Gabriel García Márquez",
            "publisher": "Editorial Sudamericana",
            "year": 1967,
            "abstract": "La historia de la familia Buendía a lo largo de siete generaciones en el pueblo ficticio de Macondo. Una obra maestra del realismo mágico que narra la soledad, el amor, la guerra y la decadencia de una estirpe marcada por el destino.",
            "tags": "realismo mágico, literatura latinoamericana, novela, García Márquez, Colombia, Macondo, familia Buendía"
        },
        {
            "title": "Don Quijote de la Mancha",
            "author": "Miguel de Cervantes",
            "publisher": "Francisco de Robles",
            "year": 1605,
            "abstract": "Las aventuras del ingenioso hidalgo Don Quijote y su escudero Sancho Panza. Considerada la primera novela moderna, es una sátira de los libros de caballerías y una reflexión sobre la realidad y la ficción.",
            "tags": "literatura española, novela, caballería, clásicos, Cervantes, Sancho Panza, aventuras"
        },
        {
            "title": "1984",
            "author": "George Orwell",
            "publisher": "Secker & Warburg",
            "year": 1949,
            "abstract": "Una distopía que presenta un futuro totalitario donde el Gran Hermano controla todos los aspectos de la vida. Una reflexión sobre el poder, la manipulación y la pérdida de la libertad individual.",
            "tags": "distopía, ciencia ficción, totalitarismo, George Orwell, Gran Hermano, control social"
        },
        {
            "title": "El amor en los tiempos del cólera",
            "author": "Gabriel García Márquez",
            "publisher": "Editorial Oveja Negra",
            "year": 1985,
            "abstract": "La historia de amor entre Florentino Ariza y Fermina Daza que se extiende por más de cincuenta años. Una reflexión sobre el amor, el paso del tiempo y la persistencia de los sentimientos.",
            "tags": "amor, romance, García Márquez, Caribe, literatura latinoamericana, tiempo"
        },
        {
            "title": "Rayuela",
            "author": "Julio Cortázar",
            "publisher": "Editorial Sudamericana",
            "year": 1963,
            "abstract": "Una novela experimental que puede leerse de múltiples formas. Narra la historia de Horacio Oliveira y su búsqueda existencial entre París y Buenos Aires.",
            "tags": "literatura experimental, Cortázar, existencialismo, París, Buenos Aires, vanguardia"
        },
        {
            "title": "La casa de los espíritus",
            "author": "Isabel Allende",
            "publisher": "Plaza & Janés",
            "year": 1982,
            "abstract": "La saga de la familia del Valle y de la Trueba a través de cuatro generaciones. Una mezcla de realismo mágico, historia política y drama familiar.",
            "tags": "realismo mágico, Isabel Allende, familia, Chile, política, mujeres"
        },
        {
            "title": "El túnel",
            "author": "Ernesto Sabato",
            "publisher": "Sur",
            "year": 1948,
            "abstract": "La confesión de Juan Pablo Castel, un pintor obsesionado que asesina a la única mujer que creía comprenderlo. Una exploración de la soledad y la incomunicación humana.",
            "tags": "existencialismo, soledad, Sabato, psicología, Argentina, obsesión"
        },
        {
            "title": "Pedro Páramo",
            "author": "Juan Rulfo",
            "publisher": "Fondo de Cultura Económica",
            "year": 1955,
            "abstract": "Juan Preciado viaja a Comala en busca de su padre, Pedro Páramo. Una obra fundamental del realismo mágico que mezcla la vida y la muerte en un pueblo fantasma.",
            "tags": "realismo mágico, Juan Rulfo, México, muerte, fantasmas, Comala"
        },
        {
            "title": "Ficciones",
            "author": "Jorge Luis Borges",
            "publisher": "Sur",
            "year": 1944,
            "abstract": "Colección de cuentos que exploran laberintos conceptuales, bibliotecas infinitas y mundos paralelos. Una obra maestra de la literatura fantástica y filosófica.",
            "tags": "cuentos, Borges, laberintos, biblioteca, filosofía, Argentina, fantástico"
        },
        {
            "title": "Crónica de una muerte anunciada",
            "author": "Gabriel García Márquez",
            "publisher": "Editorial La Oveja Negra",
            "year": 1981,
            "abstract": "La reconstrucción de un crimen de honor anunciado. Una reflexión sobre el destino, el honor y la fatalidad en una sociedad tradicional.",
            "tags": "García Márquez, honor, destino, crimen, Colombia, fatalidad"
        },
        {
            "title": "La ciudad y los perros",
            "author": "Mario Vargas Llosa",
            "publisher": "Seix Barral",
            "year": 1963,
            "abstract": "La vida en un colegio militar limeño y cómo la violencia y la corrupción moldean a los jóvenes cadetes. Una crítica a las instituciones militares y sociales.",
            "tags": "Vargas Llosa, militar, Perú, violencia, educación, Lima"
        },
        {
            "title": "El coronel no tiene quien le escriba",
            "author": "Gabriel García Márquez",
            "publisher": "Aguirre Editor",
            "year": 1961,
            "abstract": "Un coronel retirado espera infructuosamente la pensión prometida por el gobierno. Una historia sobre la dignidad, la esperanza y la pobreza.",
            "tags": "García Márquez, dignidad, pobreza, esperanza, Colombia, pensión"
        },
        {
            "title": "Los detectives salvajes",
            "author": "Roberto Bolaño",
            "publisher": "Anagrama",
            "year": 1998,
            "abstract": "La búsqueda de dos poetas por encontrar a la poetisa Cesárea Tinajero. Una exploración de la juventud, la poesía y los sueños perdidos.",
            "tags": "Bolaño, poesía, juventud, México, Chile, vanguardia"
        },
        {
            "title": "Como agua para chocolate",
            "author": "Laura Esquivel",
            "publisher": "Planeta",
            "year": 1989,
            "abstract": "La historia de Tita y su amor prohibido, contada a través de recetas de cocina. Una mezcla de realismo mágico, tradición culinaria y romance.",
            "tags": "cocina, amor, tradición, México, mujeres, realismo mágico"
        },
        {
            "title": "El laberinto de la soledad",
            "author": "Octavio Paz",
            "publisher": "Fondo de Cultura Económica",
            "year": 1950,
            "abstract": "Ensayo sobre la identidad mexicana y la condición del mexicano en el mundo moderno. Una reflexión profunda sobre la cultura y la psicología nacional.",
            "tags": "ensayo, identidad, México, cultura, Octavio Paz, psicología"
        },
        {
            "title": "La tregua",
            "author": "Mario Benedetti",
            "publisher": "Alfa",
            "year": 1960,
            "abstract": "El diario de Martín Santomé, un viudo que se enamora de una joven empleada poco antes de jubilarse. Una historia sobre el amor tardío y la soledad urbana.",
            "tags": "Benedetti, amor, soledad, Uruguay, diario, jubilación"
        },
        {
            "title": "El señor presidente",
            "author": "Miguel Ángel Asturias",
            "publisher": "Editorial Costa-Amic",
            "year": 1946,
            "abstract": "Retrato de una dictadura latinoamericana y sus efectos en la sociedad. Una denuncia del autoritarismo y la corrupción política.",
            "tags": "dictadura, política, Guatemala, Asturias, autoritarismo, corrupción"
        },
        {
            "title": "2666",
            "author": "Roberto Bolaño",
            "publisher": "Anagrama",
            "year": 2004,
            "abstract": "Cinco historias conectadas que giran en torno a una serie de crímenes en una ciudad fronteriza mexicana. Una reflexión sobre la violencia y el mal en el mundo contemporáneo.",
            "tags": "Bolaño, violencia, México, frontera, crímenes, contemporáneo"
        },
        {
            "title": "La vorágine",
            "author": "José Eustasio Rivera",
            "publisher": "Editorial Cromos",
            "year": 1924,
            "abstract": "Arturo Cova y su amante huyen a la selva amazónica donde enfrentan la explotación del caucho y la violencia. Un retrato crudo de la selva colombiana.",
            "tags": "selva, Colombia, caucho, naturaleza, Rivera, Amazonía"
        },
        {
            "title": "El reino de este mundo",
            "author": "Alejo Carpentier",
            "publisher": "EDUCA",
            "year": 1949,
            "abstract": "La revolución haitiana vista a través de los ojos del esclavo Ti Noel. Una exploración del realismo mágico y la historia caribeña.",
            "tags": "Haití, revolución, esclavitud, Carpentier, Caribe, realismo mágico"
        },
        {
            "title": "La muerte de Artemio Cruz",
            "author": "Carlos Fuentes",
            "publisher": "Fondo de Cultura Económica",
            "year": 1962,
            "abstract": "Los últimos momentos de un poderoso empresario mexicano que recuerda su vida durante la Revolución Mexicana. Una crítica al poder y la corrupción.",
            "tags": "México, revolución, poder, Fuentes, corrupción, empresario"
        },
        {
            "title": "Doña Bárbara",
            "author": "Rómulo Gallegos",
            "publisher": "Editorial Araluce",
            "year": 1929,
            "abstract": "El enfrentamiento entre la civilización y la barbarie en los llanos venezolanos. Santos Luzardo contra la cacica Doña Bárbara.",
            "tags": "Venezuela, llanos, civilización, barbarie, Gallegos, cacique"
        },
        {
            "title": "Los pasos perdidos",
            "author": "Alejo Carpentier",
            "publisher": "EDUCA",
            "year": 1953,
            "abstract": "Un musicólogo viaja a la selva sudamericana en busca de instrumentos primitivos y encuentra un mundo perdido en el tiempo.",
            "tags": "selva, música, tiempo, Carpentier, primitivo, búsqueda"
        },
        {
            "title": "El astillero",
            "author": "Juan Carlos Onetti",
            "publisher": "Compañía General Fabril Editora",
            "year": 1961,
            "abstract": "Junta Larsen regresa a Santa María para dirigir un astillero en ruinas. Una reflexión sobre el fracaso y la decadencia.",
            "tags": "Onetti, fracaso, decadencia, Uruguay, astillero, Santa María"
        },
        {
            "title": "Sobre héroes y tumbas",
            "author": "Ernesto Sabato",
            "publisher": "Compañía General Fabril Editora",
            "year": 1961,
            "abstract": "Una compleja novela que entrelaza historia argentina, psicología y filosofía a través de varios personajes en Buenos Aires.",
            "tags": "Sabato, Argentina, Buenos Aires, historia, psicología, filosofía"
        },
        {
            "title": "Terra Nostra",
            "author": "Carlos Fuentes",
            "publisher": "Joaquín Mortiz",
            "year": 1975,
            "abstract": "Una ambiciosa novela que recorre la historia de España y América desde el Renacimiento hasta el futuro. Una reflexión sobre el poder y la identidad.",
            "tags": "Fuentes, historia, España, América, poder, identidad"
        },
        {
            "title": "El recurso del método",
            "author": "Alejo Carpentier",
            "publisher": "Siglo XXI",
            "year": 1974,
            "abstract": "La historia de un dictador latinoamericano ilustrado que vive entre París y su país. Una sátira del poder autoritario y la cultura.",
            "tags": "dictadura, Carpentier, París, autoritarismo, cultura, sátira"
        },
        {
            "title": "La casa verde",
            "author": "Mario Vargas Llosa",
            "publisher": "Seix Barral",
            "year": 1966,
            "abstract": "Historias entrelazadas en la Amazonía peruana y el desierto de Piura. Una exploración de la violencia y la marginalidad en el Perú.",
            "tags": "Vargas Llosa, Amazonía, Perú, violencia, marginalidad, Piura"
        },
        {
            "title": "El obsceno pájaro de la noche",
            "author": "José Donoso",
            "publisher": "Seix Barral",
            "year": 1970,
            "abstract": "Una compleja novela sobre la decadencia de la aristocracia chilena contada desde múltiples perspectivas y voces narrativas.",
            "tags": "Donoso, Chile, aristocracia, decadencia, narrativa, perspectivas"
        },
        {
            "title": "Paradiso",
            "author": "José Lezama Lima",
            "publisher": "Ediciones Unión",
            "year": 1966,
            "abstract": "La educación sentimental de José Cemí en La Habana. Una novela barroca y compleja sobre la búsqueda del conocimiento y la belleza.",
            "tags": "Lezama Lima, Cuba, barroco, educación, belleza, conocimiento"
        },
        {
            "title": "Yo el Supremo",
            "author": "Augusto Roa Bastos",
            "publisher": "Siglo XXI",
            "year": 1974,
            "abstract": "Monólogo del dictador paraguayo José Gaspar Rodríguez de Francia. Una reflexión sobre el poder absoluto y la escritura.",
            "tags": "dictadura, Paraguay, Roa Bastos, poder, escritura, Francia"
        },
        {
            "title": "De donde son los cantantes",
            "author": "Severo Sarduy",
            "publisher": "Joaquín Mortiz",
            "year": 1967,
            "abstract": "Una exploración experimental de la identidad cubana a través del lenguaje, la música y la cultura popular.",
            "tags": "Cuba, identidad, experimental, Sarduy, música, cultura"
        },
        {
            "title": "Conversación en La Catedral",
            "author": "Mario Vargas Llosa",
            "publisher": "Seix Barral",
            "year": 1969,
            "abstract": "Un retrato de la corrupción política en el Perú durante la dictadura de Odría. Una conversación que dura cuatro horas revela toda una época.",
            "tags": "Vargas Llosa, Perú, política, corrupción, dictadura, Odría"
        },
        {
            "title": "El siglo de las luces",
            "author": "Alejo Carpentier",
            "publisher": "Compañía General de Ediciones",
            "year": 1962,
            "abstract": "La Revolución Francesa vista desde el Caribe. Una reflexión sobre las revoluciones y sus consecuencias en América Latina.",
            "tags": "revolución francesa, Caribe, Carpentier, ilustración, América Latina"
        },
        {
            "title": "La hojarasca",
            "author": "Gabriel García Márquez",
            "publisher": "Sipa",
            "year": 1955,
            "abstract": "La primera novela de García Márquez ambientada en Macondo. La historia del entierro de un médico francés odiado por el pueblo.",
            "tags": "García Márquez, Macondo, primer novela, entierro, médico, pueblo"
        },
        {
            "title": "Los ríos profundos",
            "author": "José María Arguedas",
            "publisher": "Losada",
            "year": 1958,
            "abstract": "La experiencia de un adolescente en un internado de Abancay. Una exploración del conflicto entre la cultura andina y la occidental.",
            "tags": "Arguedas, Perú, Andes, internado, cultura, adolescente"
        },
        {
            "title": "El otoño del patriarca",
            "author": "Gabriel García Márquez",
            "publisher": "Plaza & Janés",
            "year": 1975,
            "abstract": "La decadencia y muerte de un dictador caribeño que ha gobernado durante décadas. Una reflexión sobre el poder absoluto y la soledad.",
            "tags": "García Márquez, dictadura, poder, soledad, Caribe, decadencia"
        },
        {
            "title": "La región más transparente",
            "author": "Carlos Fuentes",
            "publisher": "Fondo de Cultura Económica",
            "year": 1958,
            "abstract": "Un retrato coral de la Ciudad de México en los años 50. Una exploración de las clases sociales y la modernización.",
            "tags": "Fuentes, México, Ciudad de México, clases sociales, modernización"
        },
        {
            "title": "Hijo de hombre",
            "author": "Augusto Roa Bastos",
            "publisher": "Losada",
            "year": 1960,
            "abstract": "Historias interconectadas sobre el sufrimiento y la resistencia del pueblo paraguayo. Una reflexión sobre la historia y la identidad nacional.",
            "tags": "Roa Bastos, Paraguay, sufrimiento, resistencia, historia, identidad"
        },
        {
            "title": "Respiración artificial",
            "author": "Ricardo Piglia",
            "publisher": "Pomaire",
            "year": 1980,
            "abstract": "Una novela sobre la escritura, la historia argentina y los exilios. Una reflexión metaliteraria sobre la literatura y la política.",
            "tags": "Piglia, Argentina, escritura, exilio, metaliteratura, política"
        },
        {
            "title": "Santa Evita",
            "author": "Tomás Eloy Martínez",
            "publisher": "Planeta",
            "year": 1995,
            "abstract": "La historia del cadáver embalsamado de Eva Perón y su peregrinaje por Argentina. Una mezcla de historia y ficción.",
            "tags": "Eva Perón, Argentina, cadáver, historia, ficción, Martínez"
        },
        {
            "title": "La fiesta del chivo",
            "author": "Mario Vargas Llosa",
            "publisher": "Alfaguara",
            "year": 2000,
            "abstract": "La dictadura de Rafael Trujillo en República Dominicana vista desde múltiples perspectivas. Una reflexión sobre el poder y la violencia.",
            "tags": "Vargas Llosa, Trujillo, República Dominicana, dictadura, poder, violencia"
        },
        {
            "title": "El beso de la mujer araña",
            "author": "Manuel Puig",
            "publisher": "Seix Barral",
            "year": 1976,
            "abstract": "Dos prisioneros políticos en una cárcel argentina comparten historias de películas. Una exploración de la identidad sexual y política.",
            "tags": "Puig, Argentina, prisión, cine, identidad sexual, política"
        },
        {
            "title": "La invención de Morel",
            "author": "Adolfo Bioy Casares",
            "publisher": "Sur",
            "year": 1940,
            "abstract": "Un fugitivo llega a una isla desierta donde descubre una misteriosa máquina que puede reproducir la realidad. Una obra maestra de la ciencia ficción.",
            "tags": "Bioy Casares, ciencia ficción, isla, máquina, realidad, misterio"
        },
        {
            "title": "Boquitas pintadas",
            "author": "Manuel Puig",
            "publisher": "Sudamericana",
            "year": 1969,
            "abstract": "La historia de Juan Carlos Etchepare y las mujeres que lo amaron, contada a través de cartas, tangos y folletines. Una crítica al melodrama popular.",
            "tags": "Puig, melodrama, tango, cartas, amor, folletín"
        },
        {
            "title": "Los premios",
            "author": "Julio Cortázar",
            "publisher": "Sudamericana",
            "year": 1960,
            "abstract": "Pasajeros de un crucero descubren que les está prohibido acceder a cierta parte del barco. Una alegoría sobre las restricciones sociales.",
            "tags": "Cortázar, crucero, alegoría, restricciones, social, misterio"
        },
        {
            "title": "Tres tristes tigres",
            "author": "Guillermo Cabrera Infante",
            "publisher": "Seix Barral",
            "year": 1967,
            "abstract": "La vida nocturna de La Habana antes de la Revolución Cubana. Una exploración del lenguaje, la música y la cultura popular.",
            "tags": "Cabrera Infante, Cuba, Habana, lenguaje, música, revolución"
        },
        {
            "title": "El general en su laberinto",
            "author": "Gabriel García Márquez",
            "publisher": "Mondadori",
            "year": 1989,
            "abstract": "Los últimos días de Simón Bolívar navegando por el río Magdalena hacia el exilio. Una reflexión sobre el poder, la gloria y la soledad.",
            "tags": "García Márquez, Bolívar, poder, gloria, soledad, río Magdalena"
        },
        {
            "title": "Bomarzo",
            "author": "Manuel Mujica Lainez",
            "publisher": "Sudamericana",
            "year": 1962,
            "abstract": "La vida del duque renacentista Pier Francesco Orsini y la construcción de su jardín de monstruos. Una exploración del arte y la belleza.",
            "tags": "Mujica Lainez, Renacimiento, arte, belleza, Bomarzo, monstruos"
        },
        {
            "title": "Farabeuf",
            "author": "Salvador Elizondo",
            "publisher": "Joaquín Mortiz",
            "year": 1965,
            "abstract": "Una exploración experimental del tiempo, la memoria y la tortura china del leng tch'e. Una reflexión sobre el dolor y la percepción.",
            "tags": "Elizondo, experimental, tortura, tiempo, memoria, percepción"
        }
    ]
    
    conn = get_db_connection('catalog.db')
    
    for book in books:
        # Crear indexer combinando todos los campos de texto
        indexer = f"{book['title']} {book['author']} {book.get('publisher', '')} {book.get('abstract', '')} {book.get('tags', '')}"
        
        # Crear hash único
        hash_content = f"{book['title']}{book['author']}{book.get('year', '')}"
        book_hash = generate_hash(hash_content)
        
        # Crear permalink
        permalink = f"/catalog/{book_hash}"
        
        try:
            conn.execute('''
                INSERT INTO collection (hash, permalink, title, author, publisher, year, abstract, tags, indexer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book_hash, permalink, book['title'], book['author'], 
                book.get('publisher', ''), book.get('year'), 
                book.get('abstract', ''), book.get('tags', ''), indexer
            ))
        except sqlite3.IntegrityError:
            # El libro ya existe, omitir
            print(f"Libro ya existe: {book['title']}")
            continue
    
    # Actualizar índice FTS5
    try:
        conn.execute('INSERT INTO collection_fts(collection_fts) VALUES("rebuild")')
    except:
        pass
    
    conn.commit()
    conn.close()
    
    print(f"✓ Cargados {len(books)} libros en el catálogo")

def load_library_info():
    """Carga información de ejemplo sobre la biblioteca"""
    print("Cargando información de la biblioteca...")
    
    library_info = [
        # Servicios
        {
            "title": "Préstamo de libros",
            "content": "Ofrecemos servicio de préstamo domiciliario de libros por un período de 15 días, renovable una vez si no hay reservas. Los usuarios pueden llevar hasta 3 libros simultáneamente. Es necesario presentar el carnet de la biblioteca y estar al día con las devoluciones.",
            "type": "service"
        },
        {
            "title": "Consulta en sala",
            "content": "Disponemos de amplias salas de lectura con capacidad para 200 personas. Las salas están equipadas con iluminación natural y artificial adecuada, conexión WiFi gratuita y puntos de carga para dispositivos electrónicos. El horario de consulta es de lunes a viernes de 8:00 a 20:00 horas.",
            "type": "service"
        },
        {
            "title": "Acceso a bases de datos",
            "content": "Los usuarios registrados tienen acceso a más de 50 bases de datos académicas especializadas, incluyendo JSTOR, ScienceDirect, Project MUSE y bases de datos locales. El acceso es gratuito desde las instalaciones de la biblioteca y remoto para estudiantes y profesores con credenciales válidas.",
            "type": "service"
        },
        {
            "title": "Servicio de referencia",
            "content": "Nuestros bibliotecarios especializados ofrecen asesoría personalizada para la búsqueda de información, elaboración de bibliografías y uso de recursos electrónicos. Disponible de lunes a viernes de 9:00 a 17:00 horas. También ofrecemos consultas virtuales por correo electrónico y chat.",
            "type": "service"
        },
        {
            "title": "Renovación de material",
            "content": "Los préstamos pueden renovarse una vez por el mismo período inicial, siempre que no haya reservas sobre el material. La renovación se puede hacer presencialmente, por teléfono, o a través del catálogo en línea las 24 horas del día.",
            "type": "service"
        },
        {
            "title": "Reserva de material",
            "content": "Si un libro está prestado, puedes reservarlo y te notificaremos cuando esté disponible. Las reservas se mantienen por 3 días hábiles. Puedes hacer reservas presencialmente, por teléfono o a través del catálogo en línea.",
            "type": "service"
        },
        {
            "title": "Carnet de biblioteca",
            "content": "Para obtener el carnet de biblioteca es necesario presentar documento de identidad vigente y comprobante de domicilio. El carnet es gratuito para estudiantes y profesores de la institución. Usuarios externos pueden obtenerlo con un costo anual de $50.",
            "type": "service"
        },
        {
            "title": "Fotocopiado e impresión",
            "content": "Contamos con servicio de fotocopiado e impresión disponible de lunes a viernes de 8:00 a 18:00 horas. Tarifas: fotocopia $0.10, impresión B/N $0.15, impresión color $0.50. También disponemos de escáneres de autoservicio gratuitos.",
            "type": "service"
        },
        {
            "title": "WiFi gratuito",
            "content": "Ofrecemos conexión WiFi gratuita en todas las instalaciones de la biblioteca. La red 'Biblioteca_WiFi' está disponible las 24 horas. Para acceder necesitas registrarte con tu carnet de biblioteca. Velocidad de 100 Mbps.",
            "type": "service"
        },
        {
            "title": "Préstamo interbibliotecario",
            "content": "Si no tenemos el material que necesitas, podemos solicitarlo a otras bibliotecas del país o del extranjero. El servicio tiene un costo que varía según la distancia y tipo de material. El tiempo de entrega es de 7 a 15 días hábiles.",
            "type": "service"
        },
        
        # Actividades
        {
            "title": "Club de lectura mensual",
            "content": "Cada primer viernes del mes nos reunimos para comentar un libro seleccionado previamente. Es un espacio de intercambio y análisis literario abierto a todo público. Las reuniones son a las 18:00 horas en la sala de conferencias. La participación es gratuita.",
            "type": "activity"
        },
        {
            "title": "Talleres de escritura creativa",
            "content": "Impartimos talleres de escritura creativa todos los martes de 16:00 a 18:00 horas. Dirigidos a jóvenes y adultos interesados en desarrollar sus habilidades narrativas. Los talleres incluyen ejercicios prácticos y retroalimentación grupal. Cupo limitado a 15 participantes.",
            "type": "activity"
        },
        {
            "title": "Cuentacuentos para niños",
            "content": "Todos los sábados a las 11:00 horas realizamos sesiones de cuentacuentos para niños de 4 a 8 años. Las historias se seleccionan cuidadosamente para fomentar la imaginación y el amor por la lectura. Actividad gratuita, no requiere inscripción previa.",
            "type": "activity"
        },
        {
            "title": "Conferencias magistrales",
            "content": "Organizamos conferencias mensuales con autores, académicos y personalidades del mundo cultural. Las conferencias se realizan el último jueves de cada mes a las 19:00 horas en el auditorio principal. Entrada libre hasta completar aforo.",
            "type": "activity"
        },
        {
            "title": "Exposiciones temporales",
            "content": "Regularmente organizamos exposiciones de arte, fotografía y documentos históricos en nuestra galería. Las exposiciones cambian cada dos meses y están abiertas al público durante el horario de la biblioteca. Entrada gratuita.",
            "type": "activity"
        },
        {
            "title": "Curso de alfabetización digital",
            "content": "Ofrecemos cursos gratuitos de alfabetización digital para adultos mayores todos los miércoles de 10:00 a 12:00 horas. Los participantes aprenden a usar computadoras, internet y recursos digitales básicos. Inscripciones en el mostrador principal.",
            "type": "activity"
        },
        {
            "title": "Tertulias literarias",
            "content": "Espacio de encuentro informal para amantes de la literatura que se reúnen cada viernes a las 17:00 horas. Se discuten temas diversos relacionados con libros, autores y tendencias literarias. Participación libre y gratuita.",
            "type": "activity"
        },
        {
            "title": "Maratón de lectura anual",
            "content": "Cada abril organizamos una maratón de lectura de 12 horas continuas con participación de la comunidad. Los participantes leen fragmentos de obras clásicas y contemporáneas. Incluye actividades para toda la familia y refrigerios gratuitos.",
            "type": "activity"
        },
        {
            "title": "Taller de investigación académica",
            "content": "Seminarios especializados para estudiantes universitarios sobre metodología de investigación, uso de bases de datos y citación académica. Se imparten una vez al mes los sábados de 9:00 a 13:00 horas. Requiere inscripción previa.",
            "type": "activity"
        },
        {
            "title": "Presentaciones de libros",
            "content": "Regularmente invitamos a autores locales y nacionales para presentar sus obras más recientes. Estas presentaciones incluyen lecturas, conversatorios con el público y sesiones de autógrafos. Se anuncian con anticipación en nuestras redes sociales.",
            "type": "activity"
        }
    ]
    
    conn = get_db_connection('ourlibrary.db')
    
    for info in library_info:
        # Crear indexer combinando título y contenido
        indexer = f"{info['title']} {info['content']}"
        
        # Crear hash único
        hash_content = f"{info['title']}{info['type']}"
        info_hash = generate_hash(hash_content)
        
        # Crear permalink
        permalink = f"/library/{info_hash}"
        
        try:
            conn.execute('''
                INSERT INTO infolib (hash, permalink, title, content, indexer)
                VALUES (?, ?, ?, ?, ?)
            ''', (info_hash, permalink, info['title'], info['content'], indexer))
        except sqlite3.IntegrityError:
            print(f"Info ya existe: {info['title']}")
            continue
    
    # Actualizar índice FTS5
    try:
        conn.execute('INSERT INTO infolib_fts(infolib_fts) VALUES("rebuild")')
    except:
        pass
    
    conn.commit()
    conn.close()
    
    print(f"✓ Cargados {len(library_info)} elementos de información de la biblioteca")

def load_prompts():
    """Carga los prompts del sistema"""
    print("Cargando prompts del sistema...")
    
    prompts = [
        {
            "mode": "intent",
            "type": "evaluation",
            "status": "active",
            "title": "Evaluación de intenciones",
            "content": """Eres un clasificador de intenciones para un chatbot bibliotecario. Tu tarea es analizar el mensaje del usuario y determinar cuál de estos 3 modos corresponde:

MODE1: El usuario busca libros, recomendaciones de lectura, información sobre autores, géneros literarios, o cualquier consulta relacionada con el catálogo bibliográfico.

MODE2: El usuario pregunta sobre servicios de la biblioteca (horarios, préstamos, renovaciones, carnet), actividades (talleres, eventos, conferencias) o información general sobre la biblioteca.

MODE3: El usuario quiere conversar sobre otros temas no relacionados con libros o servicios de biblioteca, hace preguntas personales, o mantiene conversación casual.

Responde ÚNICAMENTE con "mode1", "mode2" o "mode3" según corresponda. No agregues explicaciones ni texto adicional."""
        },
        {
            "mode": "mode1",
            "type": "base", 
            "status": "active",
            "title": "Prompt base para recomendaciones de libros",
            "content": """Eres LaIABot, un bibliotecario especializado en recomendaciones de libros. Tu misión es ayudar a los usuarios a encontrar las lecturas perfectas según sus gustos, necesidades e intereses.

INSTRUCCIONES:
- Mantén un tono amigable, profesional y entusiasta por la lectura
- Haz preguntas específicas para entender mejor los gustos del usuario
- Solo puedes recomendar libros que estén en nuestro catálogo
- Proporciona recomendaciones personalizadas y justificadas

IMPORTANTE: Debes responder ÚNICAMENTE en formato JSON válido como se muestra abajo. No agregues texto antes o después del JSON.

FORMATO DE RESPUESTA (ejemplo):
{
  "user_response": "¡Hola! Me encanta ayudar a encontrar el libro perfecto. Para darte mejores recomendaciones, ¿podrías contarme qué géneros te gustan más? ¿Prefieres novelas, ensayos, poesía? ¿Hay algún autor que te haya gustado especialmente?",
  "system_keywords": ["ficción", "novela", "autor específico"]
}

El campo "user_response" debe contener tu respuesta visible para el usuario.
El campo "system_keywords" debe contener palabras clave o frases para buscar libros en nuestro catálogo (máximo 5 keywords). Si no tienes suficiente información, incluye palabras generales del mensaje del usuario."""
        },
        {
            "mode": "mode1",
            "type": "suggest",
            "status": "active", 
            "title": "Prompt para sugerencias de libros",
            "content": """Eres LaIABot y te han proporcionado una lista de libros en formato APA que coinciden con lo que busca el usuario. Tu tarea es crear comentarios atractivos y personalizados para cada libro.

INSTRUCCIONES:
- Escribe comentarios breves (2-3 líneas) para cada libro
- Resalta aspectos únicos e interesantes de cada obra
- Usa un tono entusiasta que motive la lectura
- Menciona por qué cada libro podría interesar al usuario
- Mantén un estilo personal y cercano

FORMATO:
Para cada referencia bibliográfica, agrega un comentario explicativo precedido por "→".

Ejemplo:
García Márquez, G. (1967). Cien años de soledad. Editorial Sudamericana.
→ Una obra maestra del realismo mágico que te transportará al mítico pueblo de Macondo. Si te gustan las historias familiares épicas con toques fantásticos, este libro te atrapará desde la primera página.

Recuerda: Solo comenta los libros que te proporciono, no agregues otros."""
        },
        {
            "mode": "mode1", 
            "type": "follow",
            "status": "active",
            "title": "Prompt para continuar conversación sobre libros",
            "content": """Eres LaIABot continuando una conversación sobre recomendaciones de libros. Revisa el historial de la conversación para entender el contexto y las preferencias del usuario.

INSTRUCCIONES:
- Mantén continuidad con la conversación previa
- Refina las recomendaciones según las nuevas respuestas del usuario
- Profundiza en los gustos específicos revelados
- Sugiere nuevas direcciones de búsqueda si es apropiado

IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido. No agregues texto extra.

FORMATO DE RESPUESTA:
{
  "user_response": "Tu respuesta considerando el contexto de la conversación",
  "system_keywords": ["palabras", "clave", "para búsqueda"]
}

Si el usuario acepta o rechaza recomendaciones previas, ajusta las nuevas búsquedas en consecuencia. Incluye siempre keywords relevantes para buscar libros."""
        },
        {
            "mode": "mode2",
            "type": "base",
            "status": "active",
            "title": "Prompt base para información de biblioteca", 
            "content": """Eres LaIABot, especialista en servicios y actividades de nuestra biblioteca. Tu objetivo es informar a los usuarios sobre horarios, servicios, actividades, trámites y todo lo relacionado con el funcionamiento de la biblioteca.

INSTRUCCIONES:
- Sé preciso y claro en la información que proporciones
- Solo usa información que esté en nuestra base de datos
- Si no tienes la información específica, guía al usuario sobre cómo obtenerla
- Mantén un tono servicial y profesional

IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido. No agregues texto extra.

FORMATO DE RESPUESTA:
{
  "user_response": "Tu respuesta informativa para el usuario",
  "system_keywords": ["términos", "para", "buscar información"]
}

Usa "system_keywords" para buscar información específica en nuestra base de datos cuando necesites detalles precisos. Incluye términos relacionados con servicios, horarios, actividades, etc."""
        },
        {
            "mode": "mode2",
            "type": "suggest", 
            "status": "active",
            "title": "Prompt para sugerencias de información de biblioteca",
            "content": """Te han proporcionado información específica de nuestra biblioteca que responde a la consulta del usuario. Organiza y presenta esta información de manera clara y útil.

INSTRUCCIONES:
- Estructura la información de forma clara y accesible
- Resalta los datos más importantes (horarios, requisitos, costos)
- Usa un tono amigable y servicial
- Si la información es extensa, organízala en puntos clave

Presenta la información de manera que sea fácil de entender y actuar sobre ella."""
        },
        {
            "mode": "mode2",
            "type": "follow",
            "status": "active", 
            "title": "Prompt para continuar conversación sobre biblioteca",
            "content": """Continúa la conversación sobre servicios y actividades de la biblioteca considerando el historial previo.

FORMATO DE RESPUESTA JSON:
{
  "user_response": "Tu respuesta considerando el contexto previo",
  "system_keywords": ["términos", "para", "búsqueda", "específica"]
}

Ajusta la información según las necesidades específicas reveladas en la conversación."""
        },
        {
            "mode": "limits",
            "type": "base",
            "status": "active",
            "title": "Límites y directrices generales",
            "content": """Eres LaIABot, un asistente bibliotecario especializado. Estas son tus directrices fundamentales:

PUEDES HACER:
- Recomendar libros de nuestro catálogo
- Informar sobre servicios y actividades de la biblioteca  
- Mantener conversaciones amigables sobre literatura y lectura
- Ayudar con consultas académicas básicas
- Discutir autores, géneros literarios y tendencias culturales

NO PUEDES HACER:
- Proporcionar información médica, legal o financiera específica
- Dar consejos sobre problemas personales serios
- Discutir temas políticos controvertidos o sensibles
- Proporcionar información falsa o inventada
- Recomendar contenido inapropiado o ilegal

TONO Y ESTILO:
- Mantén siempre un tono profesional pero amigable
- Sé entusiasta sobre la lectura y el conocimiento
- Si no sabes algo, admítelo honestamente
- Redirige conversaciones inapropiadas hacia temas bibliotecarios

Si el usuario pregunta sobre temas fuera de tu alcance, explica amablemente tus limitaciones y sugiere alternativas relacionadas con libros o servicios de biblioteca."""
        }
    ]
    
    conn = get_db_connection('chatbot.db')
    
    for prompt in prompts:
        try:
            conn.execute('''
                INSERT INTO prompts (mode, type, status, title, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (prompt['mode'], prompt['type'], prompt['status'], prompt['title'], prompt['content']))
        except sqlite3.IntegrityError:
            print(f"Prompt ya existe: {prompt['title']}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✓ Cargados {len(prompts)} prompts del sistema")

def load_welcome_messages():
    """Carga mensajes de bienvenida"""
    print("Cargando mensajes de bienvenida...")
    
    welcome_messages = [
        "¡Hola! Soy LaIABot, tu asistente bibliotecario. ¿En qué puedo ayudarte hoy? Puedo recomendarte libros, informarte sobre nuestros servicios o simplemente charlar sobre literatura.",
        "¡Bienvenido/a! Soy LaIABot y estoy aquí para ayudarte a descubrir tu próxima lectura favorita o resolver cualquier duda sobre nuestra biblioteca. ¿Qué te interesa?",
        "¡Hola! Me llamo LaIABot y me especializo en recomendaciones de libros y servicios bibliotecarios. ¿Buscas algo específico para leer o tienes alguna consulta?",
        "¡Saludos! Soy LaIABot, tu compañero bibliotecario virtual. Estoy aquí para ayudarte a navegar por nuestro catálogo, conocer nuestros servicios o discutir sobre libros. ¿Por dónde empezamos?",
        "¡Hola! Soy LaIABot y me encanta ayudar a los lectores. Ya sea que busques una recomendación de lectura, información sobre la biblioteca o quieras conversar sobre literatura, estoy aquí para ti.",
        "¡Bienvenido/a a nuestra biblioteca! Soy LaIABot, tu asistente especializado en libros y servicios bibliotecarios. ¿Cómo puedo hacer tu visita más productiva?",
        "¡Hola! Soy LaIABot, el bibliotecario virtual que nunca descansa. Estoy aquí para ayudarte con recomendaciones de libros, dudas sobre servicios o cualquier consulta literaria. ¿Qué necesitas?",
        "¡Saludos, amante de los libros! Soy LaIABot y mi pasión es conectar lectores con las obras perfectas para ellos. También puedo ayudarte con información sobre nuestra biblioteca. ¿Qué te trae por aquí?",
        "¡Hola! Me presento: soy LaIABot, tu guía personal en el mundo de los libros y servicios bibliotecarios. ¿Hay algún género que te llame la atención o algún servicio que quieras conocer?",
        "¡Bienvenido/a! Soy LaIABot, especialista en crear conexiones mágicas entre lectores y libros. También manejo toda la información sobre nuestros servicios. ¿En qué aventura literaria puedo acompañarte?"
    ]
    
    conn = get_db_connection('chatbot.db')
    
    for message in welcome_messages:
        try:
            conn.execute('INSERT INTO welcome (content) VALUES (?)', (message,))
        except sqlite3.IntegrityError:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✓ Cargados {len(welcome_messages)} mensajes de bienvenida")

def main():
    """Función principal para cargar todos los datos de ejemplo"""
    print("=" * 60)
    print("CARGANDO DATOS DE EJEMPLO PARA LAIABOT")
    print("=" * 60)
    print()
    
    try:
        # Primero inicializar las bases de datos
        init_databases()
        print()
        
        # Crear usuario administrador
        create_admin_user()
        print()
        
        # Cargar datos del catálogo
        load_catalog_data()
        print()
        
        # Cargar información de la biblioteca
        load_library_info()
        print()
        
        # Cargar prompts del sistema
        load_prompts()
        print()
        
        # Cargar mensajes de bienvenida
        load_welcome_messages()
        print()
        
        print("=" * 60)
        print("✅ TODOS LOS DATOS SE HAN CARGADO EXITOSAMENTE")
        print("=" * 60)
        print()
        print("📚 50 libros cargados en el catálogo")
        print("🏛️ 20 elementos de información de biblioteca cargados")
        print("🤖 8 prompts del sistema configurados")
        print("👋 10 mensajes de bienvenida disponibles")
        print()
        print("🔧 Usuario administrador creado (admin/admin)")
        print()
        print("Ahora puedes ejecutar la aplicación con: python app.py")
        
    except Exception as e:
        print(f"❌ Error al cargar datos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
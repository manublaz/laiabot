
LaIABot: Agente de IA Especializado en Recomendaciones Bibliotecarias
==============================================================================

** Descripción General _______________________________________________________
==============================================================================
LaIABot es un sistema especializado de inteligencia artificial diseñado para proporcionar recomendaciones bibliotecarias personalizadas y asistencia en servicios de información documentales. Desarrollado desde una perspectiva académica en Biblioteconomía y Documentación, este agente conversacional integra técnicas avanzadas de procesamiento de lenguaje natural con metodologías tradicionales de gestión bibliotecaria.
El sistema emplea un enfoque híbrido que combina la potencia de los modelos de lenguaje grandes (LLM) con bases de datos estructuradas especializadas en catalogación bibliográfica, permitiendo ofrecer recomendaciones precisas, contextualmente relevantes y académicamente rigurosas.
Características Principales

🔍 Sistema de Recomendación Inteligente
  - Detección automática de intenciones: Clasificación en tiempo real de consultas de usuarios
  - Búsqueda híbrida FTS5+LIKE: Optimización de recuperación de información bibliográfica
  - Recomendaciones contextualizadas: Generación de sugerencias basadas en preferencias específicas
  - Referencias en formato APA: Cumplimiento de estándares académicos de citación

🗄️ Gestión Integral de Colecciones
  - Catalogación automatizada: Sistema de metadatos bibliográficos completo
  - Indexación semántica: Búsqueda de texto completo optimizada con SQLite FTS5
  - Enlaces permanentes: URLs estables para recursos bibliográficos
  - Taxonomías flexibles: Sistema de etiquetado y clasificación temática

💬 Interfaz Conversacional Avanzada
  - Modos de funcionamiento diferenciados: Recomendaciones, información de servicios y conversación general
  - Contexto persistente: Mantenimiento del historial conversacional
  - Auto-expansión inteligente: Adaptación dinámica de la interfaz según el contenido
  - Accesibilidad optimizada: Cumplimiento de estándares WCAG

🛠️ Panel de Administración Completo
  - Gestión de catálogo bibliográfico: CRUD completo para recursos documentales
  - Configuración de prompts: Personalización de comportamientos del agente
  - Monitorización de conversaciones: Análisis de interacciones y métricas de uso
  - Panel de estadísticas: Dashboard con indicadores de rendimiento del sistema


** Destinatarios y Casos de Uso ______________________________________________
==============================================================================
  Instituciones Académicas
    - Bibliotecas universitarias y de investigación
    - Centros de documentación especializada
    - Servicios de referencia académica
    - Profesionales de la Información
    - Bibliotecarios y documentalistas
    - Especialistas en sistemas de información
    - Investigadores en recuperación de información

  Usuarios Finales
    - Estudiantes universitarios y de posgrado
    - Investigadores y académicos
    - Usuarios de servicios bibliotecarios


** Arquitectura del Sistema __________________________________________________
==============================================================================
  
  ** Modos de Funcionamiento _______________________________________

  1) Recomendaciones Bibliográficas
      Usuario: "Busco libros sobre inteligencia artificial"
        ↓
      Sistema: Detección de intención + Búsqueda en catálogo
        ↓
      Respuesta: Referencias APA + Comentarios personalizados
      
  2) Modo 2: Información de Servicios
      Usuario: "¿Cuál es el horario de la biblioteca?"
        ↓
      Sistema: Búsqueda en base de datos de servicios
        ↓
      Respuesta: Información estructurada de servicios y actividades

  3) Modo 3: Conversación General
      Usuario: Consultas no especializadas
        ↓
      Sistema: Contexto conversacional + Redirección inteligente
        ↓
      Respuesta: Asistencia general con orientación hacia recursos

  ** Bases de Datos ________________________________________________
  
  catalog.db - Catálogo Bibliográfico
    collection: Tabla principal del catálogo de la biblioteca

  chatbot.db - Sistema Conversacional
    threads: Gestión de hilos de conversación
    comments: Almacenamiento de mensajes e historial
    prompts: Configuración de comportamientos del agente
    users: Gestión de usuarios y autenticación

  ourlibrary.db - Servicios Bibliotecarios
    infolib: Información de servicios, horarios y actividades

** Requisitos y Dependencias _________________________________________________
==============================================================================

Requisitos generales
  - Python: 3.8 o superior
  - Sistema Operativo: Windows, macOS, Linux
  - Memoria RAM: Mínimo 2GB, recomendado 4GB
  - Almacenamiento: 500MB libres

Dependencias Python
  - Flask==2.3.3
  - SQLite3==3.35+
  - requests==2.31.0
  - PyYAML==6.0.1
  - Werkzeug==2.3.7
  - Groq API: Para procesamiento de lenguaje natural

Otros requisitos
  - Modelo recomendado: llama3-8b-8192
  - API Key requerida


** Instalación y Configuración _______________________________________________
==============================================================================

1. Clonar el Repositorio
    bashgit clone https://github.com/usuario/laiabot.git
    cd laiabot

2. Crear Entorno Virtual
    bashpython -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate

3. Instalar Dependencias
    bashpip install -r requirements.txt

4. Configurar API Key
    Editar config.yaml:
      yamlgroq:
        api_key: "tu_api_key_aqui"
        model: "llama3-8b-8192"
        temperature: 0.7
        max_tokens: 1024

5. Inicializar Base de Datos
    bashpython install_with_samples.py
  
6. Ejecutar Aplicación
    bashpython app.py
    La aplicación estará disponible en http://localhost:5000
   
7. Credenciales de Acceso
    Panel de Administración
      Usuario: admin
      Contraseña: admin
      URL: http://localhost:5000/admin/login
      Nota: Cambiar credenciales en entorno de producción


** Flujos Conversacionales ___________________________________________________
==============================================================================

Detección de Intenciones: El sistema emplea un prompt especializado para clasificar automáticamente las consultas:

  - MODE1: Búsquedas bibliográficas, recomendaciones de lectura, 
           información sobre autores y géneros literarios.
  - MODE2: Consultas sobre servicios bibliotecarios, horarios, 
           préstamos, actividades y eventos.
  - MODE3: Conversación general relacionada con biblioteconomía,
           formativa y constructiva para los usuarios.
             
Procesamiento de Consultas
    - Análisis de intención → Clasificación automática del modo
    - Búsqueda contextual → Recuperación de información relevante
    - Generación de respuesta → Formato académico apropiado
    - Presentación estructurada → Referencias APA + comentarios

Gestión de Contexto
    - Persistencia: Mantenimiento del historial conversacional
    - Contextualización: Uso de mensajes previos para continuidad
    - Adaptación: Ajuste dinámico según el desarrollo de la conversación

Características Técnicas Avanzadas
    - Búsqueda Semántica FTS5. Implementación de SQLite FTS5 para búsquedas de texto completo optimizadas, con capacidades de ranking por relevancia y búsqueda multilingüe.
    - Sistema de Prompts Modular. Arquitectura flexible que permite la configuración de diferentes comportamientos del agente mediante prompts especializados almacenados en base de datos.
    - Referencias Bibliográficas Automatizadas. Generación automática de citas en formato APA con enlaces HTML funcionales hacia fichas bibliográficas detalladas.


Privacidad de Datos __________________________________________________________
==============================================================================
  - Almacenamiento local: No se envían datos a servicios externos excepto API Groq
  - Anonimización: No se almacenan datos personales identificables
  - Control de acceso: Segregación entre usuarios y administradores
    

** Futuras Líneas de Desarrollo ______________________________________________
==============================================================================
  - Integración con sistemas ILS/LMS existentes
  - Soporte multiidioma avanzado
  - APIs de interoperabilidad con repositorios digitales
  - Módulos de analítica avanzada de uso


** Autoría y Créditos ________________________________________________________
==============================================================================

Desarrollador Principal

  Prof. Manuel Blázquez Ochando
  Profesor Titular de Universidad
  Departamento de Biblioteconomía y Documentación
  Facultad de Ciencias de la Documentación
  Universidad Complutense de Madrid
  📧 manublaz@ucm.es
  🔗 ORCID: 0000-0002-4108-7531
  
Colaboradores en Conceptualización

  Prof. Juan José Prieto Gutiérrez
  Departamento de Biblioteconomía y Documentación
  Universidad Complutense de Madrid
  📧 jjpg@ucm.es
  🔗 ORCID: 0000-0002-1730-8621
  
  Prof. María Antonia Ovalle Perandones
  Departamento de Biblioteconomía y Documentación
  Universidad Complutense de Madrid
  📧 maovalle@ucm.es
  🔗 ORCID: 0000-0002-6149-4724


** Tecnología de IA __________________________________________________________
==============================================================================
Desarrollado utilizando Claude Sonnet 4 de Anthropic como herramienta de asistencia en el desarrollo.


** Licencia __________________________________________________________________
==============================================================================
Este proyecto se distribuye bajo licencia MIT. Consulte el archivo LICENSE para más detalles.


** Soporte y Contacto ________________________________________________________
==============================================================================
Para consultas técnicas, sugerencias de mejora o colaboraciones académicas:
  - Repositorio: GitHub - LaIABot
  - Issues: Reporte de problemas y solicitudes de características
  - Contacto académico: manublaz@ucm.es

LaIABot representa una contribución significativa a la intersección entre inteligencia artificial y ciencias de la información, 
proporcionando una herramienta práctica y académicamente sólida para la modernización de servicios bibliotecarios y documentales.

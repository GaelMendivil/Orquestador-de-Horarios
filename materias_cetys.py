"""Nombres de materias por carrera y semestre para la configuración de CETYS Tijuana.

Fuente: mapas curriculares publicados en cetys.mx (consultados el 15-nov-2026).
Los PDF son cuadrículas y su texto no conserva en qué semestre va cada materia,
salvo Psicología Organizacional. Por eso:
  - Los NOMBRES salen de los mapas oficiales siempre que fue posible.
  - El ORDEN por semestre es una propuesta nuestra (básicas primero, especialidad
    y proyectos al final), salvo Psicología Organizacional, que sigue el mapa.
  - Psicología Clínica, Psicología Infantil, Derecho, Ingeniería en Energía y
    MGDI no tuvieron lista legible: sus nombres son propuestos por nosotros,
    con el tronco común de CETYS (Ser Humano como Proyecto, Comunicación Efectiva,
    Investigación Científica, Ética..., Competencia Global).
Se usan 6 materias por semestre.

Mapas consultados:
  ICC  https://www.cetys.mx/wp-content/uploads/2022/02/40-CETYS-INGENIERIA-EN-CIENCIAS-COMPUTACIONALES-ICC.pdf
  ICE  https://www.cetys.mx/wp-content/uploads/2022/02/41-CETYS-INGENIERIA-EN-CIBERNETICA-ELECTRONICA-ICE.pdf
  IMT  https://www.cetys.mx/wp-content/uploads/2022/02/Mecatronica-1.pdf
  II   https://www.cetys.mx/en/wp-content/uploads/2022/02/Industrial-1.pdf
  IM   https://www.cetys.mx/wp-content/uploads/2022/02/Mecanica-1.pdf
  ER   https://www.cetys.mx/wp-content/uploads/2022/02/Energias-Renovables-1.pdf
  DGD  https://www.cetys.mx/wp-content/uploads/2022/02/Diseno-Grafico-Digital-1.pdf
  ISW  https://www.cetys.mx/en/wp-content/uploads/2022/02/Software-1.pdf
  LAE  https://www.cetys.mx/wp-content/uploads/2022/02/Administracion-de-empresas.pdf
  CPI  https://www.cetys.mx/en/wp-content/uploads/2022/02/Contador-Publico-Internacional-y-Finanzas-1.pdf
  LCI  https://www.cetys.mx/wp-content/uploads/2025/04/Mapa_Curricular_Logistica-y-Comercio-Internacional_2025.pdf
  NI   https://www.cetys.mx/wp-content/uploads/2022/02/Negocios-Internacionales-1.pdf
  ME   https://www.cetys.mx/en/wp-content/uploads/2022/02/Mercadotecnia-Estrategica-1.pdf
  INI  https://www.cetys.mx/wp-content/uploads/2022/02/Inteligencia-de-Negocios-e-Innovacion-1.pdf
  PSO  https://www.cetys.mx/wp-content/uploads/2025/05/PROF-28-CETYS-PSICOLOGIA-ORGANIZACIONAL-LPO_2025.pdf
"""

# --- Ingeniería -------------------------------------------------------------

ICC = {
    1: ["Cálculo Diferencial", "Fundamentos Matemáticos para Ingeniería", "Métodos de Programación",
        "Introducción a la Ingeniería en Ciencias Computacionales", "Gestión de la Información",
        "Comunicación Oral y Escrita en Español"],
    2: ["Cálculo Integral", "Matemáticas Discretas", "Lenguajes de Programación Orientada a Objetos",
        "Estática", "Ciencias de la Computación Aplicadas", "Arte y Cultura Contemporáneos"],
    3: ["Ecuaciones Diferenciales", "Estructura de Datos", "Probabilidad y Estadística", "Dinámica",
        "Diseño de Bases de Datos", "Comunicación Oral y Escrita en Inglés"],
    4: ["Métodos Numéricos", "Análisis de Algoritmos", "Sistemas de Bases de Datos", "Sistemas Operativos",
        "Gráficas y Visualización", "Globalización, Cultura y Sociedad"],
    5: ["Teoría de Autómatas", "Redes y Comunicación", "Análisis y Diseño de Sistemas",
        "Arquitectura Organizacional", "Metodología de la Investigación", "Ser Humano y Sociedad"],
    6: ["Compiladores", "Ingeniería de Software", "Aprendizaje de Máquina",
        "Desarrollo para Plataformas Heterogéneas", "Optativa I", "Ser Humano y Sustentabilidad"],
    # El 7.º semestre se reemplaza con el horario real (crear_configuraciones.py).
    7: ["Cómputo Paralelo y Distribuido", "Inteligencia Computacional", "Administración de Proyectos",
        "Administración y Seguridad de Redes", "Optativa II", "Ser Humano y Ética"],
    8: ["Proyecto Integrador de Ciencias Computacionales", "Administración de la Tecnología de la Información",
        "Optativa III", "Cómputo en la Nube", "Ciberseguridad", "Emprendimiento Tecnológico"],
}

ICE = {
    1: ["Cálculo Diferencial", "Fundamentos Matemáticos para Ingeniería", "Métodos de Programación",
        "Introducción a la Cibernética Electrónica", "Gestión de la Información",
        "Comunicación Oral y Escrita en Español"],
    2: ["Cálculo Integral", "Estática", "Electricidad y Magnetismo", "Dibujo para Ingeniería",
        "Estructura de Datos", "Arte y Cultura Contemporáneos"],
    3: ["Ecuaciones Diferenciales", "Circuitos Eléctricos", "Dinámica", "Probabilidad y Estadística",
        "Electrónica Digital I", "Comunicación Oral y Escrita en Inglés"],
    4: ["Métodos Numéricos", "Electrónica Digital II", "Electrónica Analógica I", "Arquitectura de Computadoras",
        "Diseño de Algoritmos", "Globalización, Cultura y Sociedad"],
    5: ["Señales y Sistemas", "Electrónica Analógica II", "Sistemas Operativos",
        "Microcontroladores y Sistemas Embebidos", "Metodología de la Investigación", "Ser Humano y Sociedad"],
    6: ["Ingeniería de Control", "Instrumentación Electrónica", "Redes de Computadoras", "Diseño de Interfaces",
        "Optativa I", "Ser Humano y Sustentabilidad"],
    7: ["Control Digital", "Procesamiento Digital de Señales", "Electrónica de Potencia",
        "Aplicaciones de Redes de Computadoras", "Optativa II", "Ser Humano y Ética"],
    8: ["Proyecto de Ingeniería Cibernética", "Optativa de Cómputo", "Optativa III", "Robótica",
        "Sistemas de Comunicaciones", "Administración de Proyectos"],
}

IMT = {
    1: ["Cálculo Diferencial", "Introducción a la Ingeniería", "Química para Ingeniería",
        "Dibujo para Ingeniería", "Métodos de Programación", "Ser Humano como Proyecto"],
    2: ["Cálculo Integral", "Estática", "Electricidad y Magnetismo", "Materiales para Ingeniería",
        "Probabilidad y Estadística", "Comunicación Efectiva"],
    3: ["Ecuaciones Diferenciales", "Cálculo Multivariable", "Dinámica", "Circuitos Eléctricos",
        "Lenguajes de Programación Orientado a Objetos", "Manufactura de Materiales"],
    4: ["Métodos Numéricos", "Mecánica de Materiales", "Electrónica Analógica", "Electrónica Digital",
        "Introducción al Diseño Mecánico", "Investigación Científica"],
    5: ["Modelación Matemática de Sistemas", "Dinámica de Mecanismos", "Manufactura por Computadora",
        "Microcontroladores y Sistemas Embebidos", "Tópicos de Ingeniería Económica", "Optativa I"],
    6: ["Ingeniería de Control", "Sistemas de Potencia", "Redes Industriales de Computadoras",
        "Administración de Proyectos", "Ética para la Sociedad del Siglo XXI", "Optativa II"],
    7: ["Especialización I: Automatización Industrial", "Proyecto de Aplicación I", "Certificación I",
        "Sensores y Actuadores", "Visión por Computadora", "Competencia Global"],
    8: ["Especialización II: Robótica", "Proyecto de Aplicación II", "Certificación II",
        "Control Inteligente", "Sistemas de Manufactura Flexible", "Mantenimiento Industrial"],
}

II = {
    1: ["Cálculo Diferencial", "Introducción a la Ingeniería", "Química para Ingeniería",
        "Dibujo para Ingeniería", "Métodos de Programación", "Ser Humano como Proyecto"],
    2: ["Cálculo Integral", "Estática", "Electricidad y Magnetismo", "Materiales para Ingeniería",
        "Probabilidad", "Comunicación Efectiva"],
    3: ["Ecuaciones Diferenciales", "Dinámica", "Inferencia Estadística", "Manufactura de Materiales",
        "Ingeniería Industrial", "Ingeniería de Métodos"],
    4: ["Métodos Numéricos", "Modelos de Investigación de Operaciones I", "Electrónica Industrial",
        "Ingeniería Económica", "Fabricación por Computadora", "Investigación Científica"],
    5: ["Modelos de Investigación de Operaciones II", "Ingeniería de Calidad", "Ingeniería de Sistemas de Producción",
        "Administración de Inventarios", "Administración Industrial", "Optativa I"],
    6: ["Simulación de Sistemas", "Manufactura Esbelta y Sistemas de Gestión de la Calidad",
        "Administración de la Cadena de Suministro", "Big Data Analytics",
        "Ética para la Sociedad del Siglo XXI", "Optativa II"],
    7: ["Especialización I: Ingeniería de Sistemas de Producción II", "Innovación y Desarrollo de Nuevos Productos",
        "Proyecto de Aplicación I", "Certificación I", "Ergonomía", "Competencia Global"],
    8: ["Especialización II: Tópicos de Ingeniería Industrial", "Proyecto de Aplicación II", "Certificación II",
        "Planeación de Instalaciones", "Seguridad e Higiene Industrial", "Administración de Proyectos"],
}

IM = {
    1: ["Cálculo Diferencial", "Introducción a la Ingeniería", "Química para Ingeniería",
        "Dibujo para Ingeniería I", "Álgebra Lineal", "Ser Humano como Proyecto"],
    2: ["Cálculo Integral", "Estática", "Electricidad y Magnetismo", "Dibujo para Ingeniería II",
        "Materiales para Ingeniería", "Comunicación Efectiva"],
    3: ["Ecuaciones Diferenciales", "Cálculo Multivariable", "Dinámica", "Probabilidad y Estadística",
        "Manufactura de Materiales", "Ingeniería Mecánica"],
    4: ["Métodos Numéricos", "Mecánica de Materiales", "Termodinámica", "Ingeniería de Materiales I",
        "Introducción al Diseño Mecánico", "Investigación Científica"],
    5: ["Mecánica de Fluidos", "Dinámica de Mecanismos", "Ingeniería de Materiales II",
        "Modelos Matemáticos de los Sistemas Mecánicos", "Manufactura Asistida por Computadora", "Optativa I"],
    6: ["Transferencia de Calor", "Ingeniería en Diseño", "Electroneumática e Hidráulica",
        "Análisis Experimental Mecánico", "Ética para la Sociedad del Siglo XXI", "Optativa II"],
    7: ["Especialización I: Ciclos de Potencia para Ingeniería Mecánica", "Proyecto de Aplicación I",
        "Certificación I", "Administración de Proyectos", "Vibraciones Mecánicas", "Competencia Global"],
    8: ["Especialización II: Elemento Finito", "Proyecto de Aplicación II", "Certificación II",
        "Diseño de Elementos de Máquinas", "Refrigeración y Aire Acondicionado", "Mantenimiento Industrial"],
}

ER = {
    1: ["Cálculo Diferencial", "Introducción a la Ingeniería", "Química para Ingeniería",
        "Dibujo para Ingeniería", "Programación", "Ser Humano como Proyecto"],
    2: ["Cálculo Integral", "Estática", "Electricidad y Magnetismo", "Álgebra Lineal",
        "Fuentes Renovables y Convencionales de Energía", "Comunicación Efectiva"],
    3: ["Ecuaciones Diferenciales", "Dinámica", "Probabilidad y Estadística", "Termodinámica",
        "Análisis de Circuitos Eléctricos", "Investigación Científica"],
    4: ["Mecánica de Fluidos", "Ingeniería de Materiales y Electroquímica", "Transferencia de Calor",
        "Conversión de Energía Electromecánica", "Costos e Ingeniería Económica",
        "Ética para la Sociedad del Siglo XXI"],
    5: ["Energía Solar Fotovoltaica", "Energía Solar Térmica", "Ciclos de Potencia",
        "Sistemas Electrónicos de Potencia", "Economía Energética", "Optativa I"],
    6: ["Energía Eólica", "Energía Biomasa", "Fundamentos de Control y Supervisión de Procesos",
        "Administración del Mantenimiento", "Desarrollo e Innovación", "Optativa II"],
    7: ["Especialización I: Tópicos Selectos de la Matriz Energética", "Proyecto de Aplicación I",
        "Certificación I", "Eficiencia Energética", "Redes Eléctricas Inteligentes", "Competencia Global"],
    8: ["Especialización II: Almacenamiento de Energía", "Proyecto de Aplicación II", "Certificación II",
        "Auditoría Energética", "Normatividad Energética", "Administración de Proyectos"],
}

DGD = {
    1: ["Introducción a Ingeniería en Diseño", "Dibujo Dinámico", "Composición Visual",
        "Métodos de Programación", "Fotografía Digital", "Ser Humano como Proyecto"],
    2: ["Metodología del Diseño", "Edición e Ilustración Digital", "Tipografía Digital",
        "Matemáticas para Manipulación de Imágenes", "Semiótica y Retórica Visual", "Comunicación Efectiva"],
    3: ["Programación Orientada a Objetos para Interactividad", "Modelación Geométrica", "Fundamentos de Animación",
        "Tipografía Aplicada en el Diseño Digital", "Estadística Aplicada", "Investigación Científica"],
    4: ["Modelado 3D", "Física para Animación", "Producción de Video", "Fundamentos de Experiencias de Usuario",
        "Programación de Sitios Dinámicos", "Ética para la Sociedad del Siglo XXI"],
    5: ["Animación 3D", "Gráficos en Movimiento", "Diseño de Interfaces de Usuario", "Diseño de Audio",
        "Optimización Matemática", "Optativa I"],
    6: ["Animación Dinámica", "Programación de Videojuegos", "Mercadotecnia para Redes Sociales",
        "Comercio Electrónico", "Portafolio Digital", "Optativa II"],
    7: ["Especialización I: Post-Producción Audiovisual", "Proyecto de Aplicación I", "Certificación I",
        "Dirección de Arte", "Diseño de Marca", "Competencia Global"],
    8: ["Especialización II: Producción Virtual y Realidad Extendida", "Proyecto de Aplicación II",
        "Certificación II", "Gestión de Proyectos Creativos", "Narrativa Interactiva", "Diseño Editorial Digital"],
}

ISW = {
    1: ["Cálculo Diferencial", "Introducción a la Ingeniería", "Métodos de Programación",
        "Matemáticas Discretas", "Tópicos Selectos de Química", "Ser Humano como Proyecto"],
}

IE = {  # Ingeniería en Energía: sin mapa legible, nombres propuestos.
    1: ["Cálculo Diferencial", "Introducción a la Ingeniería en Energía", "Química para Ingeniería",
        "Dibujo para Ingeniería", "Programación", "Ser Humano como Proyecto"],
}

# --- Administración y Negocios ----------------------------------------------

# Primer año común de los programas de negocios de CETYS (mismos nombres en sus mapas).
_NEG_1 = ["Administración", "Matemáticas para los Negocios", "Contabilidad Financiera", "Economía",
          "Inteligencia de Negocios", "Ser Humano como Proyecto"]
_NEG_2 = ["Contabilidad Administrativa", "Estadística de Negocios", "Derecho de los Negocios",
          "Gestión del Talento Humano", "Mercadotecnia Estratégica", "Comunicación Efectiva"]
_NEG_3 = ["Análisis Financiero", "TIC's para la Innovación Empresarial", "Derecho Laboral y Seguridad Social",
          "Investigación Científica"]

LAE = {
    1: _NEG_1, 2: _NEG_2,
    3: _NEG_3 + ["Marco Fiscal", "Genética Empresarial y Comportamiento Humano"],
    4: ["Administración Financiera", "Análisis de Mercados", "Economía Global", "Mercadotecnia de Servicios",
        "Gestión de Equipos Colaborativos de Alto Impacto", "Ética para la Sociedad del Siglo XXI"],
    5: ["Desarrollo de Emprendedores", "Administración Estratégica", "Negociación", "Administración Pública",
        "Administración de Pequeñas y Medianas Empresas", "Optativa I"],
    6: ["Innovación y Modelo de Negocios", "Innovación y Sustentabilidad Estratégica",
        "Empresas Familiares y Desarrollo Corporativo", "Optativa II", "Planeación Estratégica de Recursos",
        "Competencia Global"],
    7: ["Especialización I: Soluciones TIC para Gestión del Talento", "Proyecto de Aplicación I", "Certificación I",
        "Liderazgo Organizacional", "Gestión del Cambio", "Consultoría Empresarial"],
    8: ["Especialización II: Bienestar Integral del Talento", "Proyecto de Aplicación II", "Certificación II",
        "Gobierno Corporativo", "Simulación de Negocios", "Responsabilidad Social Empresarial"],
}

CPIyF = {
    1: _NEG_1, 2: _NEG_2,
    3: _NEG_3 + ["Contabilidad Intermedia", "Costos"],
    4: ["Contabilidad Superior", "Administración Financiera", "Derecho Tributario", "Sistemas Contemporáneos de Costos",
        "Desarrollo de Emprendedores", "Ética para la Sociedad del Siglo XXI"],
    5: ["Contabilidad Avanzada", "ISR Personas Morales", "IVA, Impuestos Especiales y Locales", "Auditoría",
        "Planeación y Control Financiero", "Optativa I"],
    6: ["Contabilidad Internacional", "Legislación Fiscal Internacional", "Prácticas de Auditoría",
        "Finanzas Corporativas", "Optativa II", "Competencia Global"],
    7: ["Especialización I: ISR Personas Físicas", "Proyecto de Aplicación I", "Certificación I",
        "Normas Internacionales de Información Financiera", "Mercados Financieros", "Seminario de Contaduría"],
    8: ["Especialización II: Servicios Bancarios y Financieros", "Proyecto de Aplicación II", "Certificación II",
        "Auditoría Fiscal", "Gobierno Corporativo", "Finanzas Bursátiles"],
}

LCI = {1: ["Introducción a la Logística y Comercio Internacional", "Administración", "Matemáticas para los Negocios",
           "Contabilidad Financiera", "Economía", "Ser Humano como Proyecto"]}

NI = {
    1: _NEG_1, 2: _NEG_2,
    3: _NEG_3 + ["Comercio Internacional", "Geografía de los Negocios Internacionales"],
    4: ["Administración Financiera", "Economía Global", "Marco Legal de los Negocios Internacionales",
        "Comportamiento Transcultural", "Mercadotecnia Internacional", "Ética para la Sociedad del Siglo XXI"],
    5: ["Finanzas Internacionales", "Administración Internacional de Aduanas", "Normatividad Internacional de Comercio",
        "Análisis de Mercados Internacionales", "Desarrollo de Emprendedores", "Optativa I"],
    6: ["Administración Estratégica Global", "Estrategia de Negociación Internacional",
        "Derecho Internacional de los Negocios", "Administración de la Cadena de Suministros", "Optativa II",
        "Competencia Global"],
    7: ["Especialización I: Desarrollo Económico Regional", "Proyecto de Aplicación I", "Certificación I",
        "Derecho Internacional del Trabajo", "Logística Internacional", "Inversión Extranjera Directa"],
    8: ["Especialización II: Tratados y Relaciones Internacionales", "Proyecto de Aplicación II", "Certificación II",
        "Seminario de Negocios Globales", "Riesgo País", "Empresas Multinacionales"],
}

# Global Program: mismo plan que NI con materias en inglés en los primeros semestres (propuesta).
NIGP = {s: list(m) for s, m in NI.items()}
NIGP[1] = ["Management", "Business Mathematics", "Financial Accounting", "Economics",
           "Business Intelligence", "Ser Humano como Proyecto"]
NIGP[2] = ["Managerial Accounting", "Business Statistics", "Business Law",
           "Human Talent Management", "Strategic Marketing", "Comunicación Efectiva"]

ME = {
    1: _NEG_1, 2: _NEG_2,
    3: _NEG_3 + ["Comportamiento del Consumidor", "Investigación de Mercados"],
    4: ["Administración Financiera", "Publicidad", "Diseño Gráfico", "Métricas de Mercadotecnia",
        "Desarrollo de Productos y Servicios", "Ética para la Sociedad del Siglo XXI"],
    5: ["Mercadotecnia Detallista", "Comercio Electrónico y Redes Sociales", "Taller de Producción Audiovisual",
        "Promoción de Ventas y Relaciones Públicas", "Desarrollo de Emprendedores", "Optativa I"],
    6: ["Mercadotecnia Internacional", "Distribución y Logística Internacional", "Liderazgo en el Equipo de Ventas",
        "Mercadotecnia Digital", "Optativa II", "Competencia Global"],
    7: ["Especialización I: Innovación en Mercadotecnia Estratégica", "Proyecto de Aplicación I", "Certificación I",
        "Gestión de Marca", "Mercadotecnia de Servicios", "Neuromarketing"],
    8: ["Especialización II: Seminario Integrador de Mercadotecnia Estratégica", "Proyecto de Aplicación II",
        "Certificación II", "Plan de Mercadotecnia", "Mercadotecnia Social", "Analítica de Clientes"],
}

INI = {
    1: ["Matemáticas", "Gestión de la Información", "Contabilidad Financiera", "Economía",
        "Teoría General de Sistemas", "Comunicación Oral y Escrita en Español"],
    2: ["Estadística", "Fundamentos de Programación y Bases de Datos", "Contabilidad Administrativa",
        "Comportamiento Humano en la Organización", "Derecho Privado", "Arte y Cultura Contemporáneos"],
    3: ["Estadística Inferencial", "Sistemas de Información para los Negocios", "Contabilidad Intermedia",
        "Gestión del Talento Humano", "Derecho Laboral y Seguridad Social", "Comunicación Oral y Escrita en Inglés"],
    4: ["Análisis Multivariante", "Inteligencia de Negocios", "Costos", "Análisis Financiero",
        "Ingeniería de Software", "Globalización, Cultura y Sociedad"],
    5: ["Ciencia de Datos", "Minería de Datos", "Administración Financiera", "Administración de Mercadotecnia",
        "Metodología de la Investigación", "Ser Humano y Sociedad"],
    6: ["Simulación de Sistemas para los Negocios", "Métodos y Modelos para la Toma de Decisiones",
        "Modelos de Desarrollo de Software", "Sistemas Complejos", "Desarrollo de Emprendedores",
        "Ser Humano y Sustentabilidad"],
    7: ["Proyectos de Inversión", "Modelo de Negocios", "Administración de Proyectos", "Administración Estratégica",
        "Optativa I", "Ser Humano y Ética"],
    8: ["Ciudadanía Global", "Optativa II", "Seminario de Innovación", "Transformación Digital",
        "Visualización de Datos para la Dirección", "Proyecto Integrador de Inteligencia de Negocios"],
}

MGDI = {1: ["Introduction to Management", "Business Mathematics", "Digital Innovation Fundamentals",
            "Financial Accounting", "Economics", "Ser Humano como Proyecto"]}

# --- Ciencias Sociales y Humanidades ------------------------------------------

PSO = {  # Sigue el mapa 2025 (5 o 6 materias por semestre; se completa a 6).
    1: ["Ser Humano como Proyecto", "Introducción a la Psicología", "Psicología y Desarrollo Social",
        "Teorías de la Personalidad", "Desarrollo de la Infancia y de la Adolescencia",
        "Optativa de Formación Integral Bloque I"],
    2: ["Comunicación Efectiva", "Estadística para las Ciencias Sociales", "Neurociencia Cognitiva de Procesos Básicos",
        "Desarrollo de la Adultez", "Desarrollo de la Sexualidad Humana", "Optativa de Formación Integral Bloque II"],
    3: ["Facilitación de Grupos", "Instrumentos de Evaluación Psicométrica",
        "Neurociencia Cognitiva de Procesos Superiores", "Técnicas de Evaluación Psicológica",
        "Psicopatología General", "Optativa de Formación Integral Bloque III"],
    4: ["Investigación Científica", "Intervención en Crisis", "Instrumentos de Evaluación de la Personalidad",
        "Psicofarmacología", "Riesgos Psicosociales en el Trabajo", "Práctica Supervisada en Prevención"],
    5: ["Intervención Cognitivo Conductual", "Elaboración de Instrumentos de Evaluación", "Gestión del Talento Humano",
        "Práctica Supervisada en Análisis y Diseño de Puestos", "Optativa I", "Optativa de Formación Integral Bloque IV"],
    6: ["Intervención Humanista", "Taller de Investigación Organizacional", "Evaluación Laboral",
        "Práctica Supervisada en Atracción y Gestión del Talento Humano", "Optativa II", "Clima y Cultura Organizacional"],
    7: ["Ética para la Sociedad del Siglo XXI", "Intervención Sistémica",
        "Especialización I: Bienestar Psicológico en el Trabajo",
        "Proyecto de Aplicación I: Práctica Supervisada en Capacitación y Desarrollo", "Certificación I",
        "Liderazgo y Equipos de Trabajo"],
    8: ["Competencia Global", "Intervención Psicodinámica", "Especialización II: Derecho Laboral",
        "Proyecto de Aplicación II: Práctica Supervisada en Desarrollo Organizacional", "Certificación II",
        "Consultoría Organizacional"],
}

# Clínica e Infantil comparten los primeros semestres con Organizacional (tronco de Psicología).
PSC = {s: list(PSO[s]) for s in (1, 2, 3)}
PSC.update({
    4: ["Investigación Científica", "Intervención en Crisis", "Instrumentos de Evaluación de la Personalidad",
        "Psicofarmacología", "Psicopatología del Adulto", "Práctica Supervisada en Prevención"],
    5: ["Intervención Cognitivo Conductual", "Entrevista Clínica", "Diagnóstico Clínico", "Psicología de la Salud",
        "Optativa I", "Optativa de Formación Integral Bloque IV"],
    6: ["Intervención Humanista", "Terapia Familiar", "Evaluación Neuropsicológica", "Práctica Supervisada en Evaluación Clínica",
        "Optativa II", "Adicciones"],
    7: ["Ética para la Sociedad del Siglo XXI", "Intervención Sistémica", "Especialización I: Psicoterapia Breve",
        "Proyecto de Aplicación I: Práctica Supervisada Clínica", "Certificación I", "Psicología Forense"],
    8: ["Competencia Global", "Intervención Psicodinámica", "Especialización II: Salud Mental Comunitaria",
        "Proyecto de Aplicación II: Práctica Supervisada en Psicoterapia", "Certificación II", "Tanatología"],
})

PSI = {s: list(PSO[s]) for s in (1, 2, 3)}
PSI.update({
    4: ["Investigación Científica", "Intervención en Crisis", "Desarrollo Cognitivo Infantil", "Psicofarmacología",
        "Psicopatología Infantil", "Práctica Supervisada en Prevención"],
    5: ["Intervención Cognitivo Conductual", "Evaluación Psicológica Infantil", "Problemas de Aprendizaje",
        "Psicología Educativa", "Optativa I", "Optativa de Formación Integral Bloque IV"],
    6: ["Terapia de Juego", "Orientación a Padres", "Trastornos del Neurodesarrollo",
        "Práctica Supervisada en Evaluación Infantil", "Optativa II", "Educación Especial e Inclusión"],
    7: ["Ética para la Sociedad del Siglo XXI", "Intervención Sistémica", "Especialización I: Intervención Temprana",
        "Proyecto de Aplicación I: Práctica Supervisada en Escuelas", "Certificación I", "Maltrato y Protección Infantil"],
    8: ["Competencia Global", "Intervención Psicodinámica", "Especialización II: Psicología del Adolescente",
        "Proyecto de Aplicación II: Práctica Supervisada en Clínica Infantil", "Certificación II",
        "Neuropsicología Infantil"],
})

DER = {  # Sin lista legible del mapa: nombres propuestos con la estructura de CETYS.
    1: ["Introducción al Estudio del Derecho", "Derecho Romano", "Teoría del Estado", "Historia del Derecho Mexicano",
        "Metodología Jurídica", "Ser Humano como Proyecto"],
    2: ["Derecho Civil: Personas y Familia", "Derecho Constitucional", "Teoría General del Proceso", "Derecho Penal I",
        "Argumentación Jurídica", "Comunicación Efectiva"],
    3: ["Derecho Civil: Bienes y Sucesiones", "Garantías Individuales y Derechos Humanos", "Derecho Procesal Civil",
        "Derecho Penal II", "Derecho Administrativo I", "Investigación Científica"],
    4: ["Derecho Civil: Obligaciones", "Derecho Mercantil I", "Derecho Procesal Penal", "Derecho Administrativo II",
        "Derecho del Trabajo", "Ética para la Sociedad del Siglo XXI"],
    5: ["Contratos Civiles", "Derecho Mercantil II", "Juicio de Amparo", "Derecho Procesal del Trabajo",
        "Derecho Fiscal", "Optativa I"],
    6: ["Títulos y Operaciones de Crédito", "Derecho Internacional Público", "Derecho Procesal Administrativo",
        "Medios Alternos de Solución de Conflictos", "Optativa II", "Competencia Global"],
    7: ["Especialización I: Derecho Corporativo", "Derecho Internacional Privado", "Proyecto de Aplicación I",
        "Certificación I", "Derecho Ambiental", "Práctica Forense Civil y Mercantil"],
    8: ["Especialización II: Litigio Oral", "Proyecto de Aplicación II", "Certificación II", "Derecho Notarial",
        "Práctica Forense Penal", "Deontología Jurídica"],
}

IIGP = {s: list(m) for s, m in II.items()}
IIGP[1] = ["Differential Calculus", "Introduction to Engineering", "Chemistry for Engineering",
           "Engineering Drawing", "Programming Methods", "Ser Humano como Proyecto"]
IIGP[2] = ["Integral Calculus", "Statics", "Electricity and Magnetism", "Engineering Materials",
           "Probability", "Comunicación Efectiva"]

MATERIAS = {
    "ICC": ICC, "ICE": ICE, "IMT": IMT, "II": II, "IIGP": IIGP, "IM": IM, "ER": ER, "DGD": DGD, "ISW": ISW,
    "IE": IE, "LAE": LAE, "CPIyF": CPIyF, "LCI": LCI, "NI": NI, "NIGP": NIGP, "ME": ME, "INI": INI,
    "MGDI": MGDI, "PSO": PSO, "PSC": PSC, "PSI": PSI, "DER": DER,
}

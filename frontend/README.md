# 🎓 Atomia Frontend - Chat Educativo con IA

Frontend web para Atomia, un sistema de educación personalizada con agentes de IA que proporciona aprendizaje adaptativo mediante atomización de contenido y evaluación inteligente.

## 🚀 Características Principales

### Chat Educativo Interactivo
- 💬 Interfaz de chat moderna y responsiva
- 🧠 Visualización del proceso de razonamiento del agente
- 📚 Atomización automática de contenido educativo
- 📊 Evaluación en tiempo real con feedback detallado

### Componentes Visuales
- **Message Bubbles**: Mensajes con soporte para Markdown
- **Atom Cards**: Tarjetas interactivas para átomos de aprendizaje
- **Agent Metadata**: Visualización del proceso de razonamiento
- **Thinking Indicator**: Animación mientras el agente procesa

## 🛠️ Stack Tecnológico

- **Framework**: Flutter 3.5+ (Web)
- **State Management**: BLoC Pattern
- **HTTP Client**: http package
- **UI Components**: Material Design 3
- **Markdown**: flutter_markdown
- **Fonts**: Google Fonts (Inter)

## 📋 Requisitos Previos

1. **Flutter SDK** 3.5 o superior
2. **Servicios Backend** ejecutándose:
   - LLM Orchestrator (puerto 8002)
   - Servicio de Atomización (puerto 8001)
   - Servicio de Evaluación (puerto 8003)

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone [repository-url]
cd frontend

# Instalar dependencias
flutter pub get

# Habilitar soporte web
flutter config --enable-web
```

## 🚀 Ejecución

### Método 1: Script automatizado
```bash
./run_web.sh
```

### Método 2: Comandos manuales
```bash
# Ejecutar en modo debug
flutter run -d chrome --web-port=5000

# Ejecutar en modo release
flutter run -d chrome --web-port=5000 --release
```

La aplicación estará disponible en: http://localhost:5000

## 📁 Estructura del Proyecto

```
lib/
├── core/                    # Núcleo de la aplicación
│   ├── api/                # Cliente HTTP y comunicación
│   ├── models/             # Modelos de datos
│   ├── services/           # Servicios principales
│   └── theme/              # Configuración de tema
├── features/               # Features por módulo
│   ├── chat/              # Feature principal de chat
│   │   ├── bloc/          # State management
│   │   ├── domain/        # Lógica de negocio
│   │   └── presentation/  # UI components
│   │       ├── pages/     # Pantallas
│   │       └── widgets/   # Widgets reutilizables
│   ├── home/              # Pantalla de inicio
│   └── learning/          # Features de aprendizaje
├── shared/                # Componentes compartidos
│   ├── widgets/          # Widgets genéricos
│   └── utils/            # Utilidades
└── main.dart             # Punto de entrada

```

## 🎨 Componentes Principales

### ChatScreen
Pantalla principal que maneja la interacción del chat educativo.

### MessageBubble
Widget para mostrar mensajes con soporte completo de Markdown.

### AtomCard
Tarjeta interactiva que muestra un átomo de aprendizaje con:
- Tipo de átomo (concepto, ejemplo, ejercicio, evaluación)
- Nivel de dificultad
- Tiempo estimado
- Objetivos de aprendizaje
- Prerrequisitos

### AgentMetadataCard
Muestra el proceso de razonamiento del agente:
- Pasos de razonamiento (Plan-Execute-Observe-Reflect)
- Herramientas utilizadas
- Confianza del agente
- Tiempo de procesamiento

### ThinkingIndicator
Indicador animado que muestra cuando el agente está procesando.

## 🔌 Integración con Backend

El frontend se comunica con tres servicios principales:

1. **LLM Orchestrator** (8002)
   - Procesamiento de consultas educativas
   - Razonamiento agéntico
   - Gestión de memoria

2. **Servicio de Atomización** (8001)
   - Descomposición de contenido
   - Creación de átomos de aprendizaje

3. **Servicio de Evaluación** (8003)
   - Evaluación de respuestas
   - Feedback personalizado
   - Seguimiento de progreso

## 🧪 Testing

```bash
# Ejecutar tests unitarios
flutter test

# Ejecutar tests con coverage
flutter test --coverage

# Ver reporte de coverage
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

## 🐛 Debugging

1. **Hot Reload**: Presiona `r` en la terminal
2. **Hot Restart**: Presiona `R` en la terminal
3. **Flutter Inspector**: Disponible en Chrome DevTools
4. **Network Inspector**: F12 en Chrome para ver llamadas API

## 🚀 Build para Producción

```bash
# Build optimizado para web
flutter build web --release

# Los archivos estarán en build/web/
```

## 📱 Características Futuras

- [ ] Modo offline con cache local
- [ ] Notificaciones push para recordatorios
- [ ] Gráficos de progreso de aprendizaje
- [ ] Exportación de sesiones de estudio
- [ ] Temas claro/oscuro
- [ ] Multi-idioma (i18n)
- [ ] Voice input/output
- [ ] Colaboración en tiempo real

## 🤝 Contribución

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Si encuentras algún problema o tienes sugerencias:
- Abre un issue en GitHub
- Contacta al equipo de desarrollo

---

**Atomia** - Transformando la educación con IA agéntica 🚀

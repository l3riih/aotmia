#!/bin/bash

# Script para ejecutar Atomia Flutter Avanzado
# Versión: 1.0.0
# Fecha: $(date)

echo "🚀 INICIANDO ATOMIA - FLUTTER AVANZADO"
echo "========================================"

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar Flutter
log_info "Verificando instalación de Flutter..."
if ! command -v flutter &> /dev/null; then
    log_error "Flutter no está instalado o no está en PATH"
    exit 1
fi

log_success "Flutter encontrado: $(flutter --version | head -n 1)"

# Verificar dispositivos disponibles
log_info "Verificando dispositivos disponibles..."
flutter devices

# Limpiar y obtener dependencias
log_info "Limpiando proyecto y obteniendo dependencias..."
flutter clean
flutter pub get

# Verificar errores de análisis
log_info "Analizando código..."
flutter analyze --no-fatal-infos --no-fatal-warnings

# Opciones de ejecución
echo ""
echo "Selecciona el modo de ejecución:"
echo "1) Web (Chrome) - Puerto 3000"
echo "2) Web (Edge) - Puerto 3000" 
echo "3) Desktop (Linux)"
echo "4) Análisis solamente"
echo "5) Tests"

read -p "Opción (1-5): " option

case $option in
    1)
        log_info "Ejecutando en Chrome en puerto 3000..."
        flutter run -d chrome --web-port 3000
        ;;
    2)
        log_info "Ejecutando en Edge en puerto 3000..."
        flutter run -d edge --web-port 3000
        ;;
    3)
        log_info "Ejecutando en Desktop Linux..."
        flutter run -d linux
        ;;
    4)
        log_info "Ejecutando análisis completo..."
        flutter analyze
        flutter test --no-sound-null-safety
        ;;
    5)
        log_info "Ejecutando tests..."
        flutter test
        ;;
    *)
        log_error "Opción inválida"
        exit 1
        ;;
esac

log_success "¡Script completado!" 
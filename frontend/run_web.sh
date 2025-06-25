#!/bin/bash

# Get the directory of the script itself.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the frontend directory.
cd "$SCRIPT_DIR" || exit

echo "🚀 Iniciando Atomia Frontend (Flutter Web)"
echo "========================================="

# Verificar que Flutter esté instalado
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter no está instalado"
    echo "Por favor instala Flutter desde: https://flutter.dev/docs/get-started/install"
    exit 1
fi

# Mostrar versión de Flutter
echo "📦 Flutter version:"
flutter --version

# Verificar dispositivos disponibles
echo -e "\n🔍 Verificando dispositivos disponibles..."
flutter devices

# Limpiar y obtener dependencias
echo -e "\n📥 Actualizando dependencias..."
flutter clean
flutter pub get

# Verificar que esté habilitado Web
echo -e "\n🌐 Verificando soporte Web..."
flutter config --enable-web

# Ejecutar en modo debug con hot reload
echo -e "\n🎯 Iniciando aplicación en modo debug..."
echo "La aplicación estará disponible en: http://localhost:5555"
echo "Presiona 'r' para hot reload, 'R' para hot restart"
echo "========================================="

flutter run -d chrome --web-port=5555
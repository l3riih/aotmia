#!/bin/bash

# Script para detener todos los servicios de Atomia
echo "🛑 Deteniendo Atomia - Sistema de Aprendizaje Agéntico"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para detener un servicio por puerto
stop_service_by_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Deteniendo $service_name (PID: $pid)...${NC}"
        kill $pid
        sleep 2
        
        # Verificar si se detuvo correctamente
        if ! lsof -ti:$port > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name detenido${NC}"
        else
            # Forzar detención si es necesario
            echo -e "${YELLOW}Forzando detención de $service_name...${NC}"
            kill -9 $pid 2>/dev/null
            echo -e "${GREEN}✓ $service_name detenido (forzado)${NC}"
        fi
    else
        echo -e "${YELLOW}○ $service_name no está corriendo${NC}"
    fi
}

# Detener Flutter
echo ""
echo "1️⃣  Deteniendo Frontend Flutter..."
echo "----------------------------------------------"

# Buscar proceso de Flutter
flutter_pid=$(pgrep -f "flutter.*run.*web-port 3000")
if [ ! -z "$flutter_pid" ]; then
    echo -e "${YELLOW}Deteniendo Flutter (PID: $flutter_pid)...${NC}"
    kill $flutter_pid
    sleep 2
    echo -e "${GREEN}✓ Flutter detenido${NC}"
else
    echo -e "${YELLOW}○ Flutter no está corriendo${NC}"
fi

# Detener servicios backend
echo ""
echo "2️⃣  Deteniendo servicios backend..."
echo "----------------------------------------------"

# Array de servicios backend
declare -A services=(
    ["api_gateway"]="8000"
    ["atomization"]="8001"
    ["llm_orchestrator"]="8002"
    ["evaluation"]="8003"
    ["planning"]="8004"
    ["questions"]="8005"
)

# Detener cada servicio
for service in "${!services[@]}"; do
    port="${services[$service]}"
    stop_service_by_port $port "$service"
done

# Limpiar logs temporales
echo ""
echo "3️⃣  Limpiando archivos temporales..."
echo "----------------------------------------------"

for service in "${!services[@]}"; do
    log_file="/tmp/${service}.log"
    if [ -f "$log_file" ]; then
        rm "$log_file"
        echo -e "${GREEN}✓ Eliminado log de $service${NC}"
    fi
done

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Todos los servicios de Atomia han sido detenidos${NC}"
echo ""
echo "Para reiniciar Atomia, ejecuta: ./scripts/start_atomia.sh"
echo "==================================================" 
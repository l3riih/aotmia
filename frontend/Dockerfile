# Dockerfile para Flutter Web
FROM ghcr.io/cirruslabs/flutter:latest

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Configurar Flutter para web
RUN flutter config --enable-web
RUN flutter config --no-analytics

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración
COPY pubspec.yaml pubspec.lock ./

# Instalar dependencias
RUN flutter pub get

# Copiar código fuente
COPY . .

# Construir la aplicación web
RUN flutter build web --release

# Usar nginx para servir la aplicación
FROM nginx:alpine
COPY --from=0 /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"] 
# Multi-stage production Dockerfile for Motorsport Incident Intelligence Frontend
# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package manifests and install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code
COPY . .

# Build arguments for configurable API base URL
ARG VITE_API_URL=/api/v1
ARG VITE_USE_LIVE_API=true
ENV VITE_API_URL=$VITE_API_URL \
    VITE_USE_LIVE_API=$VITE_USE_LIVE_API

# Build production bundle
RUN npm run build

# Stage 2: Production web server
FROM nginx:alpine as runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy production nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

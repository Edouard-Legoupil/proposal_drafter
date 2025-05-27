# Build Stage
FROM node:20-alpine AS build

# Install dependencies
RUN apk add --no-cache ca-certificates curl

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json ./

# Configure npm
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 10000 && \
    npm config set fetch-retry-maxtimeout 60000

# Install dependencies
RUN npm ci --no-audit

# Copy source code
COPY . .

# Build the application
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}
RUN npm run build

# Production Stage with Nginx
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
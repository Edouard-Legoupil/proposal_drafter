# Build Stage
FROM node:20 AS build

# Install CA certificates
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates

# 1. Update CA certificates and install curl for debugging
RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    update-ca-certificates --fresh

# 2. Configure npm to use HTTP temporarily and set retries
RUN npm config set registry http://registry.npmjs.org/ && \
    npm config set strict-ssl false && \
    npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 10000 && \
    npm config set fetch-retry-maxtimeout 60000

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
#RUN npm install

# 3. Install with error handling and fallbacks
RUN npm install || \
    (curl -v https://registry.npmjs.org > /dev/null && npm install) || \
    (sleep 10 && npm install) || \
    (npm cache clean --force && npm install)

# 4. Re-enable security after install
RUN npm config set strict-ssl true && \
    npm config set registry https://registry.npmjs.org/

# Copy source code
COPY . .

# Build the application with environment variables
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}
RUN npm run build

# Production Stage with Nginx
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
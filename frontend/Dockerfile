# frontend/Dockerfile  # Uses Debian stable with updated certs
FROM node:16-bullseye 

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

COPY package.json ./

# 3. Install with error handling and fallbacks
RUN npm install || \
    (curl -v https://registry.npmjs.org > /dev/null && npm install) || \
    (sleep 10 && npm install) || \
    (npm cache clean --force && npm install)

# 4. Re-enable security after install
RUN npm config set strict-ssl true && \
    npm config set registry https://registry.npmjs.org/

 
COPY . .

# Runs 'vite build'
CMD npm run dev



#FROM nginx:alpine
#COPY --from=builder /app/dist /usr/share/nginx/html  # Vite uses 'dist' instead of 'build'
#COPY nginx.conf /etc/nginx/conf.d/default.conf
#EXPOSE 80
#CMD ["nginx", "-g", "daemon off;"]
# frontend/Dockerfile
FROM node:16 as builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build  # Runs 'vite build'

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html  # Vite uses 'dist' instead of 'build'
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
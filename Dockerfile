# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables from .env file
ARG DEBUG
ARG SECRET_KEY
ARG ALLOWED_HOSTS
ARG DB_ENGINE
ARG DB_NAME
ARG CLOUD_NAME
ARG API_KEY
ARG API_SECRET
ARG CORS_ALLOWED_ORIGINS
ARG CSRF_TRUSTED_ORIGINS
ARG EMAIL_HOST
ARG EMAIL_PORT
ARG EMAIL_USE_TLS
ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG ${DEBUG}
ENV SECRET_KEY ${SECRET_KEY}
ENV ALLOWED_HOSTS ${ALLOWED_HOSTS}
ENV DB_ENGINE ${DB_ENGINE}
ENV DB_NAME ${DB_NAME}
ENV CLOUD_NAME ${CLOUD_NAME}
ENV API_KEY ${API_KEY}
ENV API_SECRET ${API_SECRET}
ENV CORS_ALLOWED_ORIGINS ${CORS_ALLOWED_ORIGINS}
ENV CSRF_TRUSTED_ORIGINS ${CSRF_TRUSTED_ORIGINS}
ENV EMAIL_HOST ${EMAIL_HOST}
ENV EMAIL_PORT ${EMAIL_PORT}
ENV EMAIL_USE_TLS ${EMAIL_USE_TLS}
ENV EMAIL_HOST_USER ${EMAIL_HOST_USER}
ENV EMAIL_HOST_PASSWORD ${EMAIL_HOST_PASSWORD}

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Copy entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Expose the port the app runs in
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Define the command to run the app (CMD is overridden by ENTRYPOINT)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
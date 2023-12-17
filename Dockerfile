# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables from .env file
ARG DEBUG
ARG SECRET_KEY
ARG ALLOWED_HOSTS
ARG DB_ENGINE
ARG DB_NAME

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG ${DEBUG}
ENV SECRET_KEY ${SECRET_KEY}
ENV ALLOWED_HOSTS ${ALLOWED_HOSTS}
ENV DB_ENGINE ${DB_ENGINE}
ENV DB_NAME ${DB_NAME}

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

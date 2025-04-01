# syntax=docker/dockerfile:1

# Use the official Python image as the base image
FROM python:3.11

# Define the working directory
WORKDIR /WeatherSvcApp

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Build the app layer
RUN make /WeatherSvcApp

# Expose the port the app runs on
EXPOSE 5000
EXPOSE 8080

# Command to run the application using Gunicorn
# CMD ["gunicorn",  "app:app", "-b", "0.0.0.0:5000"]
ENTRYPOINT [ "app" ]
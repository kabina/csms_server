# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the rest of the application code
COPY ./src /app

# Install gunicorn
RUN pip install gunicorn
RUN pip install flask
RUN pip install confluent_kafka
RUN pip install ocpp
RUN pip install psycopg2

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--chdir", "/app", ev_rest:app"]

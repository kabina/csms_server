# Use an official Python runtime as a parent image
FROM python:3.10

RUN useradd -ms /bin/bash 'appuser'
USER appuser

# Set the working directory to /app
WORKDIR /app

# Copy the rest of the application code
COPY ./src /app


# Create and activate a virtual environment
RUN python -m venv /home/appuser/venv
ENV PATH="/home/appuser/venv/bin:$PATH"
RUN /home/appuser/venv/bin/python -m pip install --upgrade pip

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
RUN ls /app

RUN chmod +x /app/runapp.sh
CMD ["/app/runapp.sh"]
# Run app.py when the container launches
#CMD ["gunicorn", "-b", "0.0.0.0:5000", "--chdir", "/app", ev_rest:app"]

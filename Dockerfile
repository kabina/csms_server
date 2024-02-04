# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy only the requirements.txt first to leverage Docker cache
COPY ./src/requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./src /app

# Install gunicorn
RUN pip install gunicorn

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

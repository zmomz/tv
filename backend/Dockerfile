# Set the base image
FROM python:3.10-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY backend/requirements.txt /code/requirements.txt

# Install any dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the backend code into the container
COPY ./backend /code/backend

# Set the python path to include the project root and the app directory
ENV PYTHONPATH="/code/backend"

# Command to run the application
# We use --reload-dir to watch for changes in our mounted volume
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

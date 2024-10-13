FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install pipenv
RUN pip install pipenv

# Copy the data files into the container
COPY data/crossfit_exercise_plan_01.csv ./data/crossfit_exercise_plan_01.csv
COPY data/ground-truth-retrieval.csv ./data/ground-truth-retrieval.csv

# Copy the Pipfile and Pipfile.lock into the container
COPY ["Pipfile", "Pipfile.lock", "./"]

# Install dependencies
RUN pipenv install --deploy --ignore-pipfile --system

# Copy the application code into the container
COPY fitness_assistant . 

# Expose the port
EXPOSE 5000 

# Start the application using Gunicorn
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

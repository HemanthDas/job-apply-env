FROM python:3.12-slim

WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose the port HuggingFace Spaces expects
EXPOSE 7860

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
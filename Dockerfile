# 1. Start with a reliable, specific Python server version
FROM python:3.10-slim-bullseye

# 2. Install the heavy system tools for OpenCV and Video Processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up our working folder
WORKDIR /app

# 4. Copy our shopping list and install the Python tools
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all our python scripts into the container
COPY . .

# 6. Turn on the FastAPI engine
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
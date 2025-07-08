FROM python:3.10-bullseye

# Install system dependencies and wkhtmltopdf from apt (more reliable than .deb)
RUN apt-get update && \
    apt-get install -y \
        wget \
        fontconfig \
        xfonts-75dpi \
        xfonts-base \
        xvfb \
        libjpeg-dev \
        libssl-dev \
        libxrender1 \
        libxext6 \
        libfreetype6 \
        libpng-dev \
        build-essential \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        ca-certificates \
        wkhtmltopdf \
        --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file and install Python dependencies
COPY reqs.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r reqs.txt

# Set Playwright browser path and install browsers
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN python -m playwright install --with-deps

# Copy the rest of your application code
COPY . .

CMD ["bash", "-c", "echo 'Container started. Example usage: python mca.py'; ls -l"]

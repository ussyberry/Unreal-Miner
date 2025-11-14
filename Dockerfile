# Unreal Miner - Dockerized Environment
# Multi-stage build for optimized image size

FROM osgeo/gdal:ubuntu-small-3.6.0 AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libgeos-dev \
    libproj-dev \
    openjdk-11-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="${PATH}:${JAVA_HOME}/bin"
ENV SNAP_VERSION=9.0.0
ENV SNAP_HOME=/opt/snap

# Install SNAP (Sentinel Application Platform)
FROM base AS snap-installer
WORKDIR /tmp
RUN wget -q http://step.esa.int/downloads/${SNAP_VERSION}/installers/esa-snap_sentinel_unix_${SNAP_VERSION//./_}.sh \
    && chmod +x esa-snap_sentinel_unix_${SNAP_VERSION//./_}.sh \
    && ./esa-snap_sentinel_unix_${SNAP_VERSION//./_}.sh -q -dir ${SNAP_HOME} \
    && rm esa-snap_sentinel_unix_${SNAP_VERSION//./_}.sh

# Configure SNAP
RUN ${SNAP_HOME}/bin/snap --nosplash --nogui --modules --update-all

# Final stage
FROM base
COPY --from=snap-installer ${SNAP_HOME} ${SNAP_HOME}

# Add SNAP to PATH
ENV PATH="${PATH}:${SNAP_HOME}/bin"

# Set working directory
WORKDIR /workspace

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/raw data/processed data/aligned data/outputs data/unreal_export

# Set up environment for Copernicus credentials
ENV COPERNICUS_USER=""
ENV COPERNICUS_PASSWORD=""

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
if [ -z "$COPERNICUS_USER" ] || [ -z "$COPERNICUS_PASSWORD" ]; then\n\
  echo "Warning: COPERNICUS_USER and COPERNICUS_PASSWORD not set."\n\
  echo "Set these environment variables to enable data download."\n\
fi\n\
\n\
exec "$@"\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]

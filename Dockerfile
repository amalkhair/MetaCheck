FROM python:3.12.8-bookworm
LABEL authors="Amal Khairunnisa"

ARG BUILD_DATE
ENV BUILD_DATE=$BUILD_DATE


# Combine apt-get commands to reduce layers
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y --no-install-recommends git curl postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash akmi

ENV PYTHONPATH=/home/akmi/crp/src
ENV BASE_DIR=/home/akmi/crp

WORKDIR ${BASE_DIR}


# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.


# Create and activate virtual environment
RUN python -m venv .venv
ENV APP_NAME="CRAAP Service"
ENV PATH="/home/akmi/crp/.venv/bin:$PATH"
# Copy the application into the container.
COPY src ./src
# Copy the env validator script into the image
#Temporary, will be removed later
#COPY conf ./conf
COPY pyproject.toml .
COPY README.md .
COPY uv.lock .


RUN uv venv .venv
# Install dependencies

RUN uv sync --frozen --no-cache && chown -R akmi:akmi ${BASE_DIR}
USER akmi
RUN mkdir logs
# Run the application. Validate env before starting the app.
CMD ["/bin/sh", "-c", "/home/akmi/crp/.venv/bin/python -m src.backend.craap.main"]

#CMD ["tail", "-f", "/dev/null"]
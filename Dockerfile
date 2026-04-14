# syntax=docker/dockerfile:1
# DocTranslater — multi-profile OCI images (Linux amd64/arm64 via buildx).
# Targets: runtime-base, runtime-cpu, runtime-cpu-warm, runtime-vision, runtime-vision-warm, runtime-dev
#
# Build examples:
#   docker build --target runtime-cpu -t doctranslater:cpu .
#   docker build --target runtime-cpu-warm -t doctranslater:cpu-warm .
#   docker build --target runtime-vision-warm -t doctranslater:vision-warm .

ARG PYTHON_VERSION=3.12

# --- Source (hatchling wheel metadata)
FROM python:${PYTHON_VERSION}-slim-bookworm AS src
WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY doctranslate ./doctranslate

# --- Builder: uv venv at /opt/venv (non-editable install for relocatable COPY)
FROM src AS builder-venv
RUN pip install --no-cache-dir uv \
    && uv venv /opt/venv --python "${PYTHON_VERSION}"
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

FROM builder-venv AS builder-base
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM builder-venv AS builder-cpu-sync
ARG INCLUDE_GLOSSARY=0
ARG INCLUDE_OCR=0
RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux; \
    extras="--extra pdf --extra cli --extra llm --extra tm --extra vision"; \
    if [ "$INCLUDE_OCR" = "1" ]; then extras="$extras --extra ocr"; fi; \
    if [ "$INCLUDE_GLOSSARY" = "1" ]; then extras="$extras --extra glossary"; fi; \
    uv sync --locked --no-dev --no-editable $extras

FROM builder-cpu-sync AS builder-cpu-warm
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libglib2.0-0 \
        libgomp1 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
# Warmup writes under $HOME/.cache/doctranslate (not the venv); use a fixed path to COPY into runtime.
ENV HOME=/var/lib/doctranslate-image
RUN mkdir -p "${HOME}" \
    && /opt/venv/bin/doctranslate assets warmup

FROM builder-venv AS builder-vision-sync
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --extra full

FROM builder-vision-sync AS builder-vision-warm
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        fontconfig \
        fonts-dejavu-core \
        fonts-noto-core \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libhyperscan5 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
ENV HOME=/var/lib/doctranslate-image
RUN mkdir -p "${HOME}" \
    && /opt/venv/bin/doctranslate assets warmup

FROM builder-venv AS builder-dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --group dev --extra full

# --- Runtime: base (schemas / minimal CLI)
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-base
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash doctranslater
COPY --from=builder-base /opt/venv /opt/venv
COPY docker/entrypoint.sh /docker/entrypoint.sh
RUN chmod +x /docker/entrypoint.sh
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    HOME=/home/doctranslater \
    PYTHONUNBUFFERED=1
WORKDIR /work
USER doctranslater
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD doctranslate --version || exit 1

# --- Runtime: CPU translate (layout ONNX + PDF + LLM + TM; optional OCR/glossary on builder-cpu-sync)
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-cpu
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
        fontconfig \
        fonts-dejavu-core \
        libglib2.0-0 \
        libgomp1 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash doctranslater
COPY --from=builder-cpu-sync /opt/venv /opt/venv
COPY docker/entrypoint.sh /docker/entrypoint.sh
RUN chmod +x /docker/entrypoint.sh
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    HOME=/home/doctranslater \
    PYTHONUNBUFFERED=1
WORKDIR /work
USER doctranslater
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=15s --start-period=20s --retries=3 \
    CMD doctranslate --version || exit 1

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-cpu-warm
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
        fontconfig \
        fonts-dejavu-core \
        libglib2.0-0 \
        libgomp1 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash doctranslater
COPY --from=builder-cpu-warm --chown=doctranslater:doctranslater \
    /var/lib/doctranslate-image/.cache/doctranslate \
    /home/doctranslater/.cache/doctranslate
COPY --from=builder-cpu-warm /opt/venv /opt/venv
COPY docker/entrypoint.sh /docker/entrypoint.sh
RUN chmod +x /docker/entrypoint.sh
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    HOME=/home/doctranslater \
    PYTHONUNBUFFERED=1
WORKDIR /work
USER doctranslater
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=15s --start-period=20s --retries=3 \
    CMD doctranslate --version || exit 1

# --- Runtime: full stack (CI parity: OCR, Hyperscan glossary path, vision)
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-vision
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
        fontconfig \
        fonts-dejavu-core \
        fonts-noto-core \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libhyperscan5 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash doctranslater
COPY --from=builder-vision-sync /opt/venv /opt/venv
COPY docker/entrypoint.sh /docker/entrypoint.sh
RUN chmod +x /docker/entrypoint.sh
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    HOME=/home/doctranslater \
    PYTHONUNBUFFERED=1
WORKDIR /work
USER doctranslater
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD doctranslate --version || exit 1

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-vision-warm
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
        fontconfig \
        fonts-dejavu-core \
        fonts-noto-core \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libhyperscan5 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash doctranslater
COPY --from=builder-vision-warm --chown=doctranslater:doctranslater \
    /var/lib/doctranslate-image/.cache/doctranslate \
    /home/doctranslater/.cache/doctranslate
COPY --from=builder-vision-warm /opt/venv /opt/venv
COPY docker/entrypoint.sh /docker/entrypoint.sh
RUN chmod +x /docker/entrypoint.sh
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    HOME=/home/doctranslater \
    PYTHONUNBUFFERED=1
WORKDIR /work
USER doctranslater
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD doctranslate --version || exit 1

# --- Dev / CI (pytest, ruff, mkdocs, …)
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime-dev
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
        fontconfig \
        fonts-dejavu-core \
        fonts-noto-core \
        git \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libhyperscan5 \
        libspatialindex6 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash doctranslater
COPY --from=builder-dev /opt/venv /opt/venv
COPY docker/entrypoint.sh /docker/entrypoint.sh
RUN chmod +x /docker/entrypoint.sh
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    HOME=/home/doctranslater \
    PYTHONUNBUFFERED=1
WORKDIR /work
USER doctranslater
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["--help"]
HEALTHCHECK --interval=60s --timeout=20s --start-period=60s --retries=3 \
    CMD doctranslate --version || exit 1

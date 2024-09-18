ARG BUILD_IMAGE="artefact.skao.int/ska-tango-images-pytango-builder:9.5.0"
ARG BASE_IMAGE="artefact.skao.int/ska-tango-images-pytango-runtime:9.5.0"

FROM $BUILD_IMAGE AS buildenv
FROM $BASE_IMAGE AS runtime

ARG CAR_PYPI_REPOSITORY_URL=https://artefact.skao.int/repository/pypi-internal
ENV PIP_INDEX_URL=${CAR_PYPI_REPOSITORY_URL}

USER root

WORKDIR /app

RUN mkdir -p /var/lib/slt && chown -R tango /var/lib/slt

# Copy poetry.lock* in case it doesn't exist in the repo
COPY pyproject.toml poetry.lock* ./

# Install runtime dependencies and the app
RUN poetry config virtualenvs.create false
# Developers may want to add --dev to the poetry export for testing inside a container
RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes && \
    pip install -r poetry-requirements.txt && \
    pip install . && \
    rm poetry-requirements.txt

USER tango

CMD ["fastapi", \
    "run", \
    "src/ska_oso_slt_services/app.py", \
    # Trust TLS headers set by nginx ingress:
    "--proxy-headers", \
    "--port", "5000" \
]

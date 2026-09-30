# Reproducible DevSecOps scanner image.
# Bundles the toolkit with pinned versions of the standard scanners so the
# gate runs identically on a laptop, in CI, or in a container platform.
#
# Build:  docker build -t security-toolkit:latest security-toolkit/
# Run:    docker run --rm -v "$PWD:/src" security-toolkit:latest \
#           bash cloud/cicd/pipeline_gate.sh --path /src --severity CRITICAL,HIGH
#
# For cloud CSPM, also mount your cloud creds read-only, e.g.:
#   -v "$HOME/.aws:/root/.aws:ro"
FROM python:3.12-slim

# --- Pinned tool versions -------------------------------------------------
ARG TRIVY_VERSION=0.54.1
ARG GITLEAKS_VERSION=8.18.4
ARG CHECKOV_VERSION=3.2.256
ARG PROWLER_VERSION=4.5.0

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git jq openssh-client tar \
    && rm -rf /var/lib/apt/lists/*

# Trivy (SCA, secrets, IaC, image scanning)
RUN curl -sSfL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" \
      | tar -xz -C /usr/local/bin trivy

# Gitleaks (secret scanning)
RUN curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
      | tar -xz -C /usr/local/bin gitleaks

# Python-based scanners + AWS SDK for the toolkit's AWS audits
RUN pip install \
      "checkov==${CHECKOV_VERSION}" \
      "prowler==${PROWLER_VERSION}" \
      "boto3>=1.34.0" \
      "requests>=2.31.0"

WORKDIR /toolkit
COPY . /toolkit

# Non-root by default
RUN useradd -m scanner && chown -R scanner /toolkit
USER scanner

ENTRYPOINT ["bash"]
CMD ["-lc", "cloud/cicd/pipeline_gate.sh --path /src --severity CRITICAL,HIGH"]

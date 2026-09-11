ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG BUILD_ARCH
ARG TUNNEL_CLIENT_VERSION

RUN apk add --no-cache ca-certificates python3 py3-pip unzip \
    && case "${BUILD_ARCH}" in \
         amd64) TUNNEL_ARCH="amd64"; TUNNEL_SHA256="15bd17e805cad39d412199115bb9e10a978dd35258a114cdf25dd2ae6681c7d3" ;; \
         aarch64) TUNNEL_ARCH="arm64"; TUNNEL_SHA256="2de3fb879a18edb847e0313592c912f1983685488290a7fdba7ac403e6a4fb0a" ;; \
         *) echo "unsupported architecture: ${BUILD_ARCH}" >&2; exit 1 ;; \
       esac \
    && ARCHIVE="tunnel-client-v${TUNNEL_CLIENT_VERSION}-linux-${TUNNEL_ARCH}.zip" \
    && wget -q "https://persistent.oaistatic.com/tunnel-client/v${TUNNEL_CLIENT_VERSION}/${ARCHIVE}" -O /tmp/tunnel.zip \
    && echo "${TUNNEL_SHA256}  /tmp/tunnel.zip" | sha256sum -c - \
    && unzip -j /tmp/tunnel.zip tunnel-client -d /usr/local/bin \
    && chmod 0755 /usr/local/bin/tunnel-client \
    && rm -f /tmp/tunnel.zip

WORKDIR /opt/ha-minimara
COPY rootfs/ /
COPY app/ ./
RUN python3 -m venv /opt/ha-minimara/venv \
    && /opt/ha-minimara/venv/bin/pip install --no-cache-dir --requirement requirements.txt \
    && /opt/ha-minimara/venv/bin/pip install --no-cache-dir --no-deps .

CMD ["/run.sh"]

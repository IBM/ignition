FROM python:3.7-alpine

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-{(app.port)}}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-uwsgi}

COPY whls/*.whl /whls/

RUN addgroup -S {(app.module_name)} \
 && adduser -S {(app.module_name)} -G {(app.module_name)} -u 100 \
 && mkdir -p /var/{(app.module_name)} \
 && chown -R {(app.module_name)}:{(app.module_name)} /var/{(app.module_name)} \
 && apk add --no-cache bash binutils libc-dev \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
 && for i in /whls/ignition*.whl; do if [ "$i" != "/whls/ignition*.whl" ]; then pip install --no-warn-script-location --user "$i"; fi done \
 && for i in /whls/*.whl; do pip install "$i"; done \
 && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

USER {(app.module_name)}
WORKDIR /home/{(app.module_name)}

EXPOSE {(app.port)}

CMD ["{(app.module_name)}"]
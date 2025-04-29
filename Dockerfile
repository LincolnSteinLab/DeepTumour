# PY_VERSION should be 3.X, not 3.X.X
ARG PY_VERSION=3.9

FROM python:$PY_VERSION-slim

# Create non-root user
RUN groupadd -r deeptumour && \
    useradd -r -g deeptumour deeptumour

ENV HOME="/home/deeptumour"
ENV PATH="$HOME/src:$HOME/.local/bin:$PATH"

USER deeptumour

# Copy requirements & pip install
COPY --chown=deeptumour requirements $HOME/requirements
RUN pip install --no-cache-dir -r $HOME/requirements/requirements.txt

# Copy DeepTumour code & model
COPY --chown=deeptumour src $HOME/src

WORKDIR /WORKDIR
ENTRYPOINT [ "DeepTumour.py" ]

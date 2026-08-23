ARG MAIBOT_BASE_IMAGE=sengokucola/maibot@sha256:c0d6e0430801b5c08581a3af232766ba198ae9b5c718ef0a347c39c5bb3e4c36
FROM ${MAIBOT_BASE_IMAGE}

COPY patches/graph_store_snapshot_guard.patch /tmp/graph_store_snapshot_guard.patch
RUN git -C /MaiMBot apply /tmp/graph_store_snapshot_guard.patch \
    && rm /tmp/graph_store_snapshot_guard.patch

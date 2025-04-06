#!/bin/sh -eu

if [ $# -eq 0 ]; then
  # shellcheck disable=SC2046,SC2086
  python src/main.py \
      --wallet.name "${TENSORDAEMON_WALLET}" \
      --wallet.hotkey "${TENSORDAEMON_HOTKEY}" \
      --netuid "${TENSORDAEMON_NETUID:-7}" \
      $( [ -n "${TENSORDAEMON_IP:-}" ] && echo "--axon.ip ${TENSORDAEMON_IP}" ) \
      --axon.port "${TENSORDAEMON_PORT}" \
      --axon.external_port "${TENSORDAEMON_EXTERNAL_PORT}" \
      --subtensor.network "${TENSORDAEMON_SUBTENSOR}" \
      --proxy.socket "${TENSORDAEMON_PROXY_SOCKET}"
      # ${TENSORDAEMON_EXTRA_OPTIONS}
else
  exec "$@"
fi
#!/bin/sh
# Validate edited source without replacing the running application.
set -eu
cd "$(dirname "$0")/.."
case "${1:-}" in
  --migrations) shift; mode=migrations ;;
  --startapp) shift; mode=startapp ;;
  *) mode=check ;;
esac
# A build/test process needs headroom beyond the running web and worker.
if [ -r /sys/fs/cgroup/memory.max ] && [ -r /sys/fs/cgroup/memory.current ]; then
    limit=$(cat /sys/fs/cgroup/memory.max)
    used=$(cat /sys/fs/cgroup/memory.current)
    if [ "$limit" != max ] && [ "$((limit - used))" -lt 402653184 ]; then
        echo 'Not enough memory for validation alongside the running app. Add at least 384 MiB of free memory, then retry.' >&2
        exit 1
    fi
fi
name="unistack-check-$$"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
trap 'exit 130' INT TERM
if [ "$mode" = migrations ] || [ "$mode" = startapp ]; then
    command=makemigrations
    if [ "$mode" = startapp ]; then command=startapp; fi
    timeout --foreground 300 docker compose run --name "$name" --rm --no-deps \
        --user "$(id -u):$(id -g)" -v "$PWD:/app" --entrypoint python web \
        manage.py "$command" "$@"
else
    timeout --foreground 300 docker compose run --name "$name" --rm --no-deps \
        --user "$(id -u):$(id -g)" -v "$PWD:/app" --entrypoint sh web -c \
        'python manage.py check && python manage.py makemigrations --check --dry-run && python manage.py check_site && python manage.py test "$@" --noinput' sh "$@"
fi

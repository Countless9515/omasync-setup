#!/usr/bin/env bash
# Public, credential-free launcher. The actual profile remains private on GitHub.
set -euo pipefail
umask 077

profile='Countless9515/omarchy-profile'
remote="https://github.com/${profile}.git"
cache="${XDG_CACHE_HOME:-${HOME}/.cache}/omasync-setup"

command -v mise >/dev/null || { printf 'This setup needs a fresh Omarchy installation (mise is missing).\n' >&2; exit 1; }
command -v git >/dev/null || { printf 'Git is missing; finish Omarchy installation first.\n' >&2; exit 1; }
mise use -g gh
gh_bin="$(mise which gh)"
[[ -x "${gh_bin}" ]] || { printf 'GitHub CLI did not install. Rerun this command after checking your connection.\n' >&2; exit 1; }

if ! "${gh_bin}" auth status --hostname github.com >/dev/null 2>&1; then
  printf 'Sign in to GitHub in your browser. No password or token goes in this command.\n'
  "${gh_bin}" auth login --hostname github.com --git-protocol https --web
fi
"${gh_bin}" auth status --hostname github.com >/dev/null 2>&1 || { printf 'GitHub authorization was not completed.\n' >&2; exit 1; }
"${gh_bin}" auth setup-git --hostname github.com

mkdir -p "$(dirname "${cache}")"
[[ ! -L "${cache}" ]] || { printf 'Refusing symlinked setup path: %s\n' "${cache}" >&2; exit 1; }
if [[ -e "${cache}" ]]; then
  [[ -d "${cache}/.git" ]] || { printf 'Setup path exists but is not the profile clone: %s\n' "${cache}" >&2; exit 1; }
  chmod 700 "${cache}"
  origin="$(git -C "${cache}" remote get-url origin)"
  [[ "${origin}" == "${remote}" ]] || { printf 'Refusing to update an unrelated repository: %s\n' "${origin}" >&2; exit 1; }
  git -C "${cache}" fetch --quiet origin main
  git -C "${cache}" merge --ff-only --quiet origin/main
else
  stage="$(mktemp -d "$(dirname "${cache}")/omasync-stage.XXXXXX")"
  trap 'rm -rf -- "${stage}"' EXIT
  "${gh_bin}" repo clone "${remote}" "${stage}" -- --depth 1
  mv -- "${stage}" "${cache}"
  trap - EXIT
  chmod 700 "${cache}"
fi
[[ -f "${cache}/install.sh" ]] || { printf 'The private profile did not contain its installer.\n' >&2; exit 1; }
exec bash "${cache}/install.sh" laptop

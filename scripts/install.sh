#!/usr/bin/env bash
# Ownership-manifest installer for codecraft-skills.
#
# Installs the skill catalog into an agent's skill directory using a
# per-target ownership manifest kept OUTSIDE the shipped surface
# (~/.config/codecraft/<target>.manifest.tsv), so the promise holds:
# each target directory gains only <skill>/SKILL.md files.
#
# Usage:
#   scripts/install.sh install [--target opencode|claude] [--skills a,b,c] [--dry-run]
#   scripts/install.sh doctor   [--target opencode|claude]
#   scripts/install.sh uninstall [--target opencode|claude] [--dry-run]
#
# Requires bash + coreutils. Hashing uses sha256sum, falling back to shasum.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${HOME}/.config/codecraft"

ALL_SKILLS=(
  refactor-methods refactor-objects refactor-data refactor-conditionals
  refactor-calls refactor-generalization patterns-creational
  patterns-structural patterns-behavioral refactor-detect patterns-detect
)

TARGET="opencode"
DEST=""
MANIFEST=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
codecraft-skills installer

Usage:
  scripts/install.sh install [--target opencode|claude] [--skills a,b,c] [--dry-run]
  scripts/install.sh doctor   [--target opencode|claude]
  scripts/install.sh uninstall [--target opencode|claude] [--dry-run]

Targets: opencode -> ~/.agents/skills, claude -> ~/.claude/skills.
Manifest: ~/.config/codecraft/<target>.manifest.tsv (ownership + sha256).
USAGE
}

die() { echo "error: $*" >&2; exit 1; }

hash_file() {
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | cut -d' ' -f1
  else
    die "neither sha256sum nor shasum is available"
  fi
}

resolve_target() {
  case "$1" in
    opencode) echo "${HOME}/.agents/skills" ;;
    claude)   echo "${HOME}/.claude/skills" ;;
    *) die "unknown target '$1' (expected opencode or claude)" ;;
  esac
}

parse_opts() {
  TARGET="opencode"
  DRY_RUN=0
  local skills_csv=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --target)  TARGET="${2:?--target needs a value}"; shift ;;
      --skills)  skills_csv="${2:?--skills needs a value}"; shift ;;
      --dry-run) DRY_RUN=1 ;;
      -h|--help) usage; exit 0 ;;
      *) die "unknown option '$1'" ;;
    esac
    shift
  done
  DEST="$(resolve_target "$TARGET")"
  MANIFEST="${CONFIG_DIR}/${TARGET}.manifest.tsv"
  PARSED_SKILLS_CSV="$skills_csv"
}

declare -A M_HASH=() M_DST=()

load_manifest() {
  [[ -f "$MANIFEST" ]] || return 0
  local line skill dst h
  while IFS=$'\t' read -r skill dst h _rest; do
    M_HASH["$skill"]="$h"
    M_DST["$skill"]="$dst"
  done < "$MANIFEST"
}

save_manifest() {
  local tmp="${MANIFEST}.tmp"
  {
    for skill in $(printf '%s\n' "${!M_DST[@]}" | sort); do
      printf '%s\t%s\t%s\n' "$skill" "${M_DST[$skill]}" "${M_HASH[$skill]}"
    done
  } > "$tmp"
  mv "$tmp" "$MANIFEST"
}

cmd_install() {
  parse_opts "$@"
  local -a skills=()
  if [[ -n "${PARSED_SKILLS_CSV:-}" ]]; then
    IFS=',' read -ra skills <<< "${PARSED_SKILLS_CSV}"
  else
    skills=("${ALL_SKILLS[@]}")
  fi
  local bad="" s
  for s in "${skills[@]}"; do
    [[ -f "${REPO_ROOT}/${s}/SKILL.md" ]] || bad+="$s "
  done
  [[ -z "$bad" ]] || die "not found in repo: ${bad}"

  load_manifest
  local skipped_conflict=0
  for s in "${skills[@]}"; do
    local src="${REPO_ROOT}/${s}/SKILL.md"
    local dst="${DEST}/${s}/SKILL.md"
    local new_hash
    new_hash="$(hash_file "$src")"
    if [[ -e "$dst" && -z "${M_HASH[$s]:-}" ]]; then
      echo "SKIP  ${s}: ${dst} exists and is not owned by this installer"
      skipped_conflict=$((skipped_conflict + 1))
      continue
    fi
    if [[ "$DRY_RUN" == 1 ]]; then
      echo "WOULD INSTALL  ${s} -> ${dst}"
    elif [[ "${M_HASH[$s]:-}" == "$new_hash" ]]; then
      echo "UNCHANGED  ${s}"
    else
      mkdir -p "$(dirname "$dst")"
      cp "$src" "$dst"
      echo "INSTALLED  ${s} -> ${dst}"
    fi
    M_HASH["$s"]="$new_hash"
    M_DST["$s"]="$dst"
  done
  if [[ "$DRY_RUN" != 1 ]]; then
    mkdir -p "$CONFIG_DIR"
    save_manifest
  fi
  echo "install done: ${#skills[@]} selected, ${skipped_conflict} skipped (unowned conflicts), dry-run=${DRY_RUN}"
}

cmd_doctor() {
  parse_opts "$@"
  [[ -f "$MANIFEST" ]] || die "no manifest at ${MANIFEST} (run install first)"
  load_manifest
  local rc=0 ok_count=0 skill dst mhash ihash rhash
  local n=${#M_DST[@]}
  if [[ "$n" -eq 0 ]]; then
    echo "doctor: manifest is empty; nothing installed"
    return 0
  fi
  for skill in $(printf '%s\n' "${!M_DST[@]}" | sort); do
    dst="${M_DST[$skill]}"
    mhash="${M_HASH[$skill]}"
    if [[ ! -f "$dst" ]]; then
      echo "MISSING  ${skill} (${dst})"
      rc=1
      continue
    fi
    ihash="$(hash_file "$dst")"
    if [[ "$ihash" != "$mhash" ]]; then
      echo "DRIFTED  ${skill} (installed file differs from manifest)"
      rc=1
      continue
    fi
    if [[ -f "${REPO_ROOT}/${skill}/SKILL.md" ]]; then
      rhash="$(hash_file "${REPO_ROOT}/${skill}/SKILL.md")"
      if [[ "$rhash" != "$mhash" ]]; then
        echo "STALE    ${skill} (repo changed since install; rerun install)"
        rc=1
        continue
      fi
    fi
    echo "OK       ${skill}"
    ok_count=$((ok_count + 1))
  done
  echo "doctor: ${ok_count}/${n} healthy"
  return "$rc"
}

cmd_uninstall() {
  parse_opts "$@"
  [[ -f "$MANIFEST" ]] || die "no manifest at ${MANIFEST}; nothing owned to remove"
  load_manifest
  local skill removed=0 kept=0
  local n=${#M_DST[@]}
  if [[ "$n" -eq 0 ]]; then
    echo "uninstall: manifest is empty; nothing to remove"
    return 0
  fi
  for skill in $(printf '%s\n' "${!M_DST[@]}" | sort); do
    local dst="${M_DST[$skill]}" mhash="${M_HASH[$skill]}" cur
    if [[ ! -f "$dst" ]]; then
      unset "M_DST[$skill]" "M_HASH[$skill]"
      continue
    fi
    cur="$(hash_file "$dst")"
    if [[ "$cur" != "$mhash" ]]; then
      if [[ "$DRY_RUN" == 1 ]]; then
        echo "WOULD KEEP   ${dst} (modified since install)"
      else
        echo "KEEPING    ${dst} (modified since install; remove manually if intended)"
      fi
      kept=$((kept + 1))
      unset "M_DST[$skill]" "M_HASH[$skill]"
      continue
    fi
    if [[ "$DRY_RUN" == 1 ]]; then
      echo "WOULD REMOVE  ${dst}"
    else
      rm "$dst"
      find "$(dirname "$dst")" -type f | grep -q . || rmdir "$(dirname "$dst")" 2>/dev/null || true
      echo "REMOVED   ${dst}"
    fi
    removed=$((removed + 1))
    unset "M_DST[$skill]" "M_HASH[$skill]"
  done
  if [[ "$DRY_RUN" != 1 ]]; then
    if [[ ${#M_DST[@]} -eq 0 ]]; then
      rm -f "$MANIFEST"
    else
      save_manifest
    fi
    rmdir "$CONFIG_DIR" 2>/dev/null || true
  fi
  echo "uninstall done: ${removed} removed, ${kept} kept (local modifications), dry-run=${DRY_RUN}"
}

main() {
  local cmd="${1:-help}"
  if [[ $# -gt 0 ]]; then shift; fi
  case "$cmd" in
    install)   cmd_install "$@" ;;
    doctor)    cmd_doctor "$@" ;;
    uninstall) cmd_uninstall "$@" ;;
    help|-h|--help) usage ;;
    *) die "unknown command '${cmd}' (expected install, doctor, uninstall)" ;;
  esac
}

main "$@"

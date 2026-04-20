#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/paper-build.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

MAIN_DOC="${PAPER_DIR}/manuscript.md"
REFS_DOC="${TMP_DIR}/90_references.md"
APPENDICES_DOC="${TMP_DIR}/99_appendices.md"
OUTPUT_DIR="${PAPER_DIR}/output"
OUTPUT_PATH="${1:-${OUTPUT_DIR}/paper.pdf}"

mkdir -p "${OUTPUT_DIR}"

cat > "${REFS_DOC}" <<'EOF'
# СПИСОК ЛИТЕРАТУРЫ И ИНТЕРНЕТ-РЕСУРСОВ

```{=typst}
#set bibliography(title: none)
#bibliography(
  "metadata/references.bib",
  style: "metadata/csl/gost-r-7-0-100-2018-numeric-appearance.csl",
)
```
EOF

appendix_letters=(А Б В Г Д Е Ж И К Л М Н)

if compgen -G "${PAPER_DIR}/appendices/*.md" > /dev/null; then
  appendix_index=0
  : > "${APPENDICES_DOC}"

  for appendix in "${PAPER_DIR}"/appendices/*.md; do
    if (( appendix_index >= ${#appendix_letters[@]} )); then
      echo "Too many appendices for the configured lettering scheme." >&2
      exit 1
    fi

    appendix_letter="${appendix_letters[appendix_index]}"
    awk -v letter="${appendix_letter}" '
      BEGIN {
        replaced = 0
        print "# ПРИЛОЖЕНИЕ " letter
        print ""
      }
      !replaced && /^# / {
        sub(/^# /, "### ")
        replaced = 1
      }
      { print }
    ' "${appendix}" >> "${APPENDICES_DOC}"

    printf '\n\n' >> "${APPENDICES_DOC}"
    appendix_index=$((appendix_index + 1))
  done
fi

PANDOC_INPUTS=(
  "${MAIN_DOC}"
  "${REFS_DOC}"
)

if [[ -f "${APPENDICES_DOC}" ]]; then
  PANDOC_INPUTS+=("${APPENDICES_DOC}")
fi

RELATIVE_INPUTS=()
for input_path in "${PANDOC_INPUTS[@]}"; do
  if [[ "${input_path}" == "${PAPER_DIR}/"* ]]; then
    RELATIVE_INPUTS+=("${input_path#"${PAPER_DIR}/"}")
  else
    RELATIVE_INPUTS+=("${input_path}")
  fi
done

(
  cd "${PAPER_DIR}"
  pandoc \
    --defaults metadata/defaults.yaml \
    --lua-filter metadata/filters/code-listings.lua \
    --lua-filter metadata/filters/citations-footnotes.lua \
    "${RELATIVE_INPUTS[@]}" \
    -o "${OUTPUT_PATH}"
)

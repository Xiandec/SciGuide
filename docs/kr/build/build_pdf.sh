#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KR_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/kr-build.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

MAIN_DOC="${KR_DIR}/Galimov_PM23-2.md"
REFS_DOC="${TMP_DIR}/90_references.md"
APPENDICES_DOC="${TMP_DIR}/99_appendices.md"
OUTPUT_PATH="${1:-${KR_DIR}/Galimov_PM23-2.pdf}"

cat > "${REFS_DOC}" <<'EOF'
# СПИСОК ЛИТЕРАТУРЫ И ИНТЕРНЕТ-РЕСУРСОВ

```{=typst}
#set bibliography(title: none)
#bibliography(
  "build/references.bib",
  style: "build/gost-r-7-0-100-2018-numeric-appearance.csl",
)
```
EOF

appendix_letters=(А Б В Г Д Е Ж И К Л М Н)

if compgen -G "${KR_DIR}/appendices/*.md" > /dev/null; then
  appendix_index=0
  : > "${APPENDICES_DOC}"

  for appendix in "${KR_DIR}"/appendices/*.md; do
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
  if [[ "${input_path}" == "${KR_DIR}/"* ]]; then
    RELATIVE_INPUTS+=("${input_path#"${KR_DIR}/"}")
  else
    RELATIVE_INPUTS+=("${input_path}")
  fi
done

(
  cd "${KR_DIR}"
  pandoc \
    --defaults build/defaults.yaml \
    --lua-filter build/filters/code-listings.lua \
    --lua-filter build/filters/citations-footnotes.lua \
    "${RELATIVE_INPUTS[@]}" \
    -o "${OUTPUT_PATH}"
)

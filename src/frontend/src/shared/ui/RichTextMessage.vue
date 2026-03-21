<script setup>
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import katex from 'katex'
import MarkdownIt from 'markdown-it'
import texmath from 'markdown-it-texmath'

import 'katex/dist/katex.min.css'

const props = defineProps({
  content: {
    type: String,
    default: '',
  },
})

function normalizeLatexDelimiters(content) {
  return (content || '')
    .replace(/\\\[((?:.|\n)+?)\\\]/g, '\n$$$1$$\n')
    .replace(/\\\(((?:.|\n)+?)\\\)/g, '$$$1$$')
}

const markdown = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  typographer: true,
})

markdown.use(texmath, {
  engine: katex,
  delimiters: 'dollars',
  katexOptions: {
    throwOnError: false,
    strict: 'ignore',
  },
})

const defaultLinkOpen =
  markdown.renderer.rules.link_open ||
  function renderLinkOpen(tokens, index, options, env, self) {
    return self.renderToken(tokens, index, options)
  }

markdown.renderer.rules.link_open = function renderSafeLinkOpen(tokens, index, options, env, self) {
  const token = tokens[index]

  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer nofollow')

  return defaultLinkOpen(tokens, index, options, env, self)
}

const renderedContent = computed(() =>
  DOMPurify.sanitize(markdown.render(normalizeLatexDelimiters(props.content))),
)
</script>

<template>
  <div class="rich-text" v-html="renderedContent" />
</template>

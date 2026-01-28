<script setup>
/**
 * AgentCard - Individual agent response display
 *
 * Shows an agent's contribution to a deliberation round.
 */

import { computed } from 'vue'

const props = defineProps({
  agentId: {
    type: String,
    required: true,
  },
  content: {
    type: String,
    default: '',
  },
  inputTokens: {
    type: Number,
    default: 0,
  },
  outputTokens: {
    type: Number,
    default: 0,
  },
  color: {
    type: String,
    default: '#888888',
  },
  isStreaming: {
    type: Boolean,
    default: false,
  },
})

const totalTokens = computed(() => props.inputTokens + props.outputTokens)

// Simple markdown-like formatting for paragraphs
const formattedContent = computed(() => {
  if (!props.content) return ''
  return props.content
    .split('\n\n')
    .map(p => `<p class="mb-3 last:mb-0">${p.replace(/\n/g, '<br>')}</p>`)
    .join('')
})
</script>

<template>
  <div
    class="card p-4 flex flex-col"
    :style="{ borderTopColor: color, borderTopWidth: '3px' }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm"
          :style="{ backgroundColor: color + '30', color: color }"
        >
          {{ agentId[0] }}
        </div>
        <span class="font-medium" :style="{ color: color }">{{ agentId }}</span>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span v-if="isStreaming" class="flex items-center gap-1">
          <span class="w-2 h-2 bg-gold rounded-full animate-pulse"></span>
          typing...
        </span>
        <span v-else>{{ totalTokens }} tok</span>
      </div>
    </div>

    <!-- Content -->
    <div
      class="flex-1 text-sm text-gray-300 leading-relaxed prose prose-invert prose-sm max-w-none"
      v-html="formattedContent"
    ></div>

    <!-- Footer -->
    <div class="flex items-center justify-between mt-3 pt-3 border-t border-apex-border text-xs text-gray-500">
      <span>In: {{ inputTokens }}</span>
      <span>Out: {{ outputTokens }}</span>
    </div>
  </div>
</template>

<style scoped>
.card {
  @apply bg-apex-card border border-apex-border rounded-xl;
}

.card :deep(p) {
  @apply text-gray-300;
}

.card :deep(strong) {
  @apply text-white font-semibold;
}
</style>

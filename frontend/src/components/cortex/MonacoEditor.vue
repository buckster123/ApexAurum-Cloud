<script setup>
/**
 * Monaco Editor Wrapper for Cortex Diver
 *
 * Provides syntax highlighting, code editing, and AI integration hooks.
 */

import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as monaco from 'monaco-editor'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  language: {
    type: String,
    default: 'plaintext',
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
  theme: {
    type: String,
    default: 'cortex-dark',
  },
  filename: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'save', 'selection-change', 'cursor-change'])

const editorContainer = ref(null)
let editor = null
let model = null

// Custom Cortex Diver theme
function defineTheme() {
  monaco.editor.defineTheme('cortex-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A6A6A', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'FFD700' },  // Gold
      { token: 'string', foreground: 'A5D6A7' },   // Green
      { token: 'number', foreground: 'F48FB1' },   // Pink
      { token: 'type', foreground: '81D4FA' },     // Blue
      { token: 'function', foreground: 'CE93D8' }, // Purple
      { token: 'variable', foreground: 'FFCC80' }, // Orange
    ],
    colors: {
      'editor.background': '#0D0D0D',
      'editor.foreground': '#E0E0E0',
      'editor.lineHighlightBackground': '#1A1A1A',
      'editor.selectionBackground': '#3D3D00',
      'editorCursor.foreground': '#FFD700',
      'editorLineNumber.foreground': '#4A4A4A',
      'editorLineNumber.activeForeground': '#FFD700',
      'editor.inactiveSelectionBackground': '#2A2A00',
      'editorIndentGuide.background': '#2A2A2A',
      'editorIndentGuide.activeBackground': '#3A3A3A',
      'editorWidget.background': '#141414',
      'editorWidget.border': '#3A3A3A',
      'editorSuggestWidget.background': '#141414',
      'editorSuggestWidget.border': '#FFD70033',
      'editorSuggestWidget.selectedBackground': '#2A2A00',
    },
  })
}

onMounted(() => {
  defineTheme()

  // Create model
  model = monaco.editor.createModel(
    props.modelValue,
    props.language
  )

  // Create editor
  editor = monaco.editor.create(editorContainer.value, {
    model,
    theme: props.theme,
    readOnly: props.readOnly,
    automaticLayout: true,
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
    fontLigatures: true,
    lineNumbers: 'on',
    minimap: { enabled: true, maxColumn: 80 },
    scrollBeyondLastLine: false,
    wordWrap: 'off',
    tabSize: 2,
    insertSpaces: true,
    cursorStyle: 'line',
    cursorBlinking: 'smooth',
    smoothScrolling: true,
    renderWhitespace: 'selection',
    bracketPairColorization: { enabled: true },
    guides: {
      bracketPairs: true,
      indentation: true,
    },
    padding: { top: 10, bottom: 10 },
  })

  // Listen for content changes
  model.onDidChangeContent(() => {
    emit('update:modelValue', model.getValue())
  })

  // Listen for selection changes (for AI context)
  editor.onDidChangeCursorSelection((e) => {
    const selection = editor.getSelection()
    const selectedText = model.getValueInRange(selection)
    emit('selection-change', {
      text: selectedText,
      range: {
        startLine: selection.startLineNumber,
        startColumn: selection.startColumn,
        endLine: selection.endLineNumber,
        endColumn: selection.endColumn,
      },
    })
  })

  // Listen for cursor position changes
  editor.onDidChangeCursorPosition((e) => {
    emit('cursor-change', {
      line: e.position.lineNumber,
      column: e.position.column,
    })
  })

  // Add Ctrl+S save shortcut
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
    emit('save')
  })

  // Add context menu action for AI
  editor.addAction({
    id: 'ask-agent',
    label: 'Ask Agent About Selection',
    keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyA],
    contextMenuGroupId: 'navigation',
    contextMenuOrder: 1,
    run: () => {
      const selection = editor.getSelection()
      const selectedText = model.getValueInRange(selection)
      if (selectedText) {
        emit('selection-change', {
          text: selectedText,
          range: {
            startLine: selection.startLineNumber,
            startColumn: selection.startColumn,
            endLine: selection.endLineNumber,
            endColumn: selection.endColumn,
          },
          action: 'ask-agent',
        })
      }
    },
  })
})

onUnmounted(() => {
  if (editor) {
    editor.dispose()
  }
  if (model) {
    model.dispose()
  }
})

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (model && newValue !== model.getValue()) {
    model.setValue(newValue)
  }
})

// Watch for language changes
watch(() => props.language, (newLanguage) => {
  if (model) {
    monaco.editor.setModelLanguage(model, newLanguage)
  }
})

// Watch for read-only changes
watch(() => props.readOnly, (readOnly) => {
  if (editor) {
    editor.updateOptions({ readOnly })
  }
})

// Expose methods for parent
function focus() {
  editor?.focus()
}

function insertText(text, position = null) {
  if (!editor) return
  const pos = position || editor.getPosition()
  editor.executeEdits('insert', [{
    range: new monaco.Range(pos.lineNumber, pos.column, pos.lineNumber, pos.column),
    text,
  }])
}

function replaceSelection(text) {
  if (!editor) return
  const selection = editor.getSelection()
  editor.executeEdits('replace', [{
    range: selection,
    text,
  }])
}

function getSelectedText() {
  if (!editor || !model) return ''
  return model.getValueInRange(editor.getSelection())
}

defineExpose({
  focus,
  insertText,
  replaceSelection,
  getSelectedText,
})
</script>

<template>
  <div ref="editorContainer" class="w-full h-full"></div>
</template>

<style>
/* Monaco editor container styling */
.monaco-editor {
  border-radius: 0;
}

.monaco-editor .margin {
  background-color: #0D0D0D !important;
}
</style>

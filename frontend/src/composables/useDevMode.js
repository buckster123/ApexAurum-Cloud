import { ref, onMounted, onUnmounted } from 'vue'

// Singleton state - shared across all components
const devMode = ref(localStorage.getItem('devMode') === 'true')

// Konami code sequence: ↑↑↓↓←→←→BA
const KONAMI_CODE = [
  'ArrowUp', 'ArrowUp',
  'ArrowDown', 'ArrowDown',
  'ArrowLeft', 'ArrowRight',
  'ArrowLeft', 'ArrowRight',
  'KeyB', 'KeyA'
]

export function useDevMode() {
  const konamiIndex = ref(0)
  const tapCount = ref(0)
  const tapTimeout = ref(null)

  // Toggle dev mode
  function enableDevMode() {
    devMode.value = true
    localStorage.setItem('devMode', 'true')
    console.log('🔧 Dev Mode activated!')
  }

  function disableDevMode() {
    devMode.value = false
    localStorage.removeItem('devMode')
    console.log('Dev Mode deactivated')
  }

  function toggleDevMode() {
    if (devMode.value) {
      disableDevMode()
    } else {
      enableDevMode()
    }
  }

  // Konami code detection
  function handleKeyDown(event) {
    const expectedKey = KONAMI_CODE[konamiIndex.value]

    if (event.code === expectedKey) {
      konamiIndex.value++

      if (konamiIndex.value === KONAMI_CODE.length) {
        // Konami code complete!
        enableDevMode()
        konamiIndex.value = 0
      }
    } else {
      // Reset on wrong key
      konamiIndex.value = 0
    }
  }

  // 7-tap detection for an element
  function handleTap() {
    tapCount.value++

    // Clear previous timeout
    if (tapTimeout.value) {
      clearTimeout(tapTimeout.value)
    }

    // Check if 7 taps reached
    if (tapCount.value >= 7) {
      enableDevMode()
      tapCount.value = 0
      return
    }

    // Reset after 2 seconds of no taps
    tapTimeout.value = setTimeout(() => {
      tapCount.value = 0
    }, 2000)
  }

  // Setup and cleanup
  function setupKonamiListener() {
    window.addEventListener('keydown', handleKeyDown)
  }

  function cleanupKonamiListener() {
    window.removeEventListener('keydown', handleKeyDown)
  }

  // Auto-setup when using in a component
  onMounted(() => {
    setupKonamiListener()
  })

  onUnmounted(() => {
    cleanupKonamiListener()
    if (tapTimeout.value) {
      clearTimeout(tapTimeout.value)
    }
  })

  return {
    devMode,
    enableDevMode,
    disableDevMode,
    toggleDevMode,
    handleTap,
    tapCount,
    setupKonamiListener,
    cleanupKonamiListener
  }
}

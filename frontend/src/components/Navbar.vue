<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const mobileMenuOpen = ref(false)

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <nav class="fixed top-0 left-0 right-0 h-16 bg-apex-dark/80 backdrop-blur-lg border-b border-apex-border z-50">
    <div class="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/chat" class="flex items-center gap-2">
        <span class="text-2xl font-serif font-bold text-gold">Au</span>
        <span class="hidden sm:inline text-lg font-medium">ApexAurum</span>
      </router-link>

      <!-- Desktop Navigation -->
      <div class="hidden md:flex items-center gap-6">
        <router-link
          to="/chat"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Chat
        </router-link>
        <router-link
          to="/agents"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Agents
        </router-link>
        <router-link
          to="/village"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Village
        </router-link>
        <router-link
          to="/music"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Music
        </router-link>
        <router-link
          to="/files"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Files
        </router-link>
        <router-link
          to="/neural"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Neural
        </router-link>
        <router-link
          to="/village-gui"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          GUI
        </router-link>
        <router-link
          to="/billing"
          class="text-gray-400 hover:text-white transition-colors"
          active-class="text-gold"
        >
          Billing
        </router-link>
      </div>

      <!-- Desktop User Menu -->
      <div class="hidden md:flex items-center gap-4">
        <router-link
          to="/settings"
          class="text-gray-400 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
          </svg>
        </router-link>

        <button
          @click="handleLogout"
          class="btn-ghost text-sm text-gray-400 hover:text-white"
        >
          Logout
        </button>
      </div>

      <!-- Mobile Menu Button -->
      <button
        @click="mobileMenuOpen = !mobileMenuOpen"
        class="md:hidden p-2 text-gray-400 hover:text-white transition-colors"
      >
        <!-- Hamburger icon -->
        <svg
          v-if="!mobileMenuOpen"
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <!-- Close icon -->
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Mobile Menu Dropdown -->
    <div
      v-if="mobileMenuOpen"
      class="md:hidden absolute top-16 left-0 right-0 bg-apex-dark border-b border-apex-border shadow-xl"
    >
      <div class="flex flex-col p-4 space-y-1">
        <router-link
          to="/chat"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          💬 Chat
        </router-link>
        <router-link
          to="/agents"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          🤖 Agents
        </router-link>
        <router-link
          to="/village"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          🏘️ Village
        </router-link>
        <router-link
          to="/music"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          🎵 Music
        </router-link>
        <router-link
          to="/files"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          📁 Files
        </router-link>
        <router-link
          to="/neural"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          🧠 Neural
        </router-link>
        <router-link
          to="/village-gui"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          👁️ GUI
        </router-link>
        <router-link
          to="/billing"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          💳 Billing
        </router-link>

        <hr class="border-apex-border my-2" />

        <router-link
          to="/settings"
          @click="closeMobileMenu"
          class="px-4 py-3 rounded-lg text-gray-300 hover:bg-white/5 hover:text-gold transition-colors"
        >
          ⚙️ Settings
        </router-link>
        <button
          @click="handleLogout"
          class="px-4 py-3 rounded-lg text-left text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
        >
          🚪 Logout
        </button>
      </div>
    </div>
  </nav>
</template>

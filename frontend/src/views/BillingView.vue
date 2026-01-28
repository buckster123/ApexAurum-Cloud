<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useBillingStore } from '@/stores/billing'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const billing = useBillingStore()
const auth = useAuthStore()

const activeTab = ref('plans')
const loadingAction = ref(null)
const couponCode = ref('')
const couponMessage = ref(null)

// Check for success redirect
const checkoutSuccess = computed(() => route.query.session_id)

onMounted(async () => {
  await billing.fetchStatus()
  await billing.fetchPricing()

  if (checkoutSuccess.value) {
    // Refresh status after successful checkout
    setTimeout(() => billing.fetchStatus(), 2000)
  }
})

async function selectPlan(tierId) {
  if (tierId === 'free') return
  if (tierId === billing.status.tier) return

  loadingAction.value = tierId
  try {
    await billing.createSubscriptionCheckout(tierId)
  } catch (e) {
    console.error('Checkout error:', e)
  } finally {
    loadingAction.value = null
  }
}

async function buyCredits(packId) {
  loadingAction.value = `credits-${packId}`
  try {
    await billing.createCreditsCheckout(packId)
  } catch (e) {
    console.error('Checkout error:', e)
  } finally {
    loadingAction.value = null
  }
}

async function manageSubscription() {
  loadingAction.value = 'portal'
  try {
    await billing.openPortal()
  } catch (e) {
    console.error('Portal error:', e)
  } finally {
    loadingAction.value = null
  }
}

async function redeemCoupon() {
  if (!couponCode.value.trim()) return

  couponMessage.value = null
  loadingAction.value = 'coupon'

  try {
    const result = await billing.redeemCoupon(couponCode.value.trim())
    couponMessage.value = {
      success: true,
      text: result.benefit_description,
    }
    couponCode.value = ''
  } catch (e) {
    couponMessage.value = {
      success: false,
      text: billing.error || 'Failed to redeem coupon',
    }
  } finally {
    loadingAction.value = null
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="text-center mb-12">
      <h1 class="text-4xl font-bold mb-4">Choose Your Path</h1>
      <p class="text-gray-400 text-lg">
        From Seeker to Adept, unlock the full power of the Athanor
      </p>
    </div>

    <!-- Success Message -->
    <div v-if="checkoutSuccess" class="mb-8 bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
      <div class="text-green-400 text-lg font-medium">Payment Successful!</div>
      <p class="text-green-300/70 text-sm mt-1">Your account is being updated...</p>
    </div>

    <!-- Current Status Card -->
    <div v-if="auth.isAuthenticated" class="mb-12 bg-surface rounded-xl p-6 border border-gold/20">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div class="text-sm text-gray-400 mb-1">Current Plan</div>
          <div class="text-2xl font-bold text-gold">{{ billing.tierName }}</div>
          <div class="text-sm text-gray-500 mt-1">
            {{ `$${billing.status.tier === 'free' ? '3' : billing.status.tier === 'pro' ? '10' : '30'}/month` }}
          </div>
        </div>

        <div class="flex items-center gap-6">
          <!-- Usage -->
          <div v-if="billing.status.messages_limit" class="text-center">
            <div class="text-sm text-gray-400 mb-1">Messages Used</div>
            <div class="text-xl font-semibold">
              {{ billing.status.messages_used }} / {{ billing.status.messages_limit }}
            </div>
            <div class="w-32 h-2 bg-gray-700 rounded-full mt-2 overflow-hidden">
              <div
                class="h-full transition-all duration-300"
                :class="{
                  'bg-green-500': billing.usagePercent < 60,
                  'bg-yellow-500': billing.usagePercent >= 60 && billing.usagePercent < 90,
                  'bg-red-500': billing.usagePercent >= 90
                }"
                :style="{ width: `${billing.usagePercent}%` }"
              ></div>
            </div>
          </div>
          <div v-else class="text-center">
            <div class="text-sm text-gray-400 mb-1">Messages</div>
            <div class="text-xl font-semibold text-gold">Unlimited</div>
          </div>

          <!-- Credits -->
          <div class="text-center">
            <div class="text-sm text-gray-400 mb-1">Credits</div>
            <div class="text-xl font-semibold">${{ billing.status.credit_balance_usd.toFixed(2) }}</div>
          </div>

          <!-- Manage Button -->
          <button
            v-if="billing.status.tier !== 'free'"
            @click="manageSubscription"
            :disabled="loadingAction === 'portal'"
            class="px-4 py-2 bg-surface border border-gray-600 rounded-lg hover:border-gold/50 transition-colors disabled:opacity-50"
          >
            {{ loadingAction === 'portal' ? 'Loading...' : 'Manage Subscription' }}
          </button>
        </div>
      </div>

      <!-- Period End Warning -->
      <div v-if="billing.status.cancel_at_period_end" class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400 text-sm">
        Your subscription will end on {{ formatDate(billing.status.current_period_end) }}
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex justify-center mb-8">
      <div class="inline-flex bg-surface rounded-lg p-1 border border-gray-700">
        <button
          @click="activeTab = 'plans'"
          :class="[
            'px-6 py-2 rounded-md transition-colors',
            activeTab === 'plans' ? 'bg-gold text-black font-medium' : 'text-gray-400 hover:text-white'
          ]"
        >
          Subscription Plans
        </button>
        <button
          @click="activeTab = 'credits'"
          :class="[
            'px-6 py-2 rounded-md transition-colors',
            activeTab === 'credits' ? 'bg-gold text-black font-medium' : 'text-gray-400 hover:text-white'
          ]"
        >
          Credit Packs
        </button>
        <button
          v-if="auth.isAuthenticated"
          @click="activeTab = 'history'; billing.fetchTransactions()"
          :class="[
            'px-6 py-2 rounded-md transition-colors',
            activeTab === 'history' ? 'bg-gold text-black font-medium' : 'text-gray-400 hover:text-white'
          ]"
        >
          History
        </button>
      </div>
    </div>

    <!-- Plans Tab -->
    <div v-if="activeTab === 'plans'" class="grid md:grid-cols-3 gap-6">
      <div
        v-for="tier in (billing.pricing?.tiers || [])"
        :key="tier.id"
        :class="[
          'relative rounded-xl p-6 border transition-all',
          tier.popular
            ? 'bg-gold/5 border-gold shadow-lg shadow-gold/10'
            : 'bg-surface border-gray-700 hover:border-gray-600',
          billing.status.tier === tier.id && 'ring-2 ring-gold/50'
        ]"
      >
        <!-- Popular Badge -->
        <div
          v-if="tier.popular"
          class="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold text-black text-xs font-bold px-3 py-1 rounded-full"
        >
          MOST POPULAR
        </div>

        <!-- Current Badge -->
        <div
          v-if="billing.status.tier === tier.id"
          class="absolute -top-3 right-4 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full"
        >
          CURRENT
        </div>

        <!-- Header -->
        <div class="text-center mb-6">
          <h3 class="text-2xl font-bold mb-1">{{ tier.name }}</h3>
          <p class="text-gray-400 text-sm">{{ tier.tagline }}</p>
          <div class="mt-4">
            <span class="text-4xl font-bold">${{ tier.price_monthly }}</span>
            <span v-if="tier.price_monthly > 0" class="text-gray-400">/mo</span>
            <span v-else class="text-gray-400 text-sm ml-1">forever</span>
          </div>
          <div class="text-sm text-gray-500 mt-1">
            {{ tier.messages_per_month ? `${tier.messages_per_month.toLocaleString()} messages/month` : 'Unlimited messages' }}
          </div>
        </div>

        <!-- Features -->
        <ul class="space-y-3 mb-6">
          <li v-for="feature in tier.features" :key="feature" class="flex items-start gap-2 text-sm">
            <svg class="w-5 h-5 text-gold flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            <span class="text-gray-300">{{ feature }}</span>
          </li>
        </ul>

        <!-- CTA Button -->
        <button
          @click="selectPlan(tier.id)"
          :disabled="tier.id === 'free' || billing.status.tier === tier.id || loadingAction === tier.id"
          :class="[
            'w-full py-3 rounded-lg font-medium transition-all',
            tier.popular
              ? 'bg-gold text-black hover:bg-gold/90'
              : 'bg-surface border border-gray-600 hover:border-gold/50',
            (tier.id === 'free' || billing.status.tier === tier.id) && 'opacity-50 cursor-not-allowed'
          ]"
        >
          {{
            loadingAction === tier.id
              ? 'Processing...'
              : billing.status.tier === tier.id
                ? 'Current Plan'
                : tier.id === 'free'
                  ? 'Free'
                  : `Upgrade to ${tier.name}`
          }}
        </button>
      </div>
    </div>

    <!-- Credits Tab -->
    <div v-if="activeTab === 'credits'" class="max-w-2xl mx-auto">
      <div class="text-center mb-8">
        <h2 class="text-2xl font-bold mb-2">Credit Packs</h2>
        <p class="text-gray-400">
          Credits are used when you exceed your monthly message limit.
          They never expire and can be used with any model.
        </p>
      </div>

      <div class="grid md:grid-cols-2 gap-6">
        <div
          v-for="pack in (billing.pricing?.credit_packs || [])"
          :key="pack.id"
          class="bg-surface rounded-xl p-6 border border-gray-700 hover:border-gold/30 transition-all"
        >
          <div class="text-center">
            <h3 class="text-xl font-bold mb-1">{{ pack.name }}</h3>
            <div class="text-3xl font-bold text-gold mb-2">${{ pack.price_usd }}</div>
            <div class="text-gray-400 mb-4">
              {{ pack.credits.toLocaleString() }} credits
              <span v-if="pack.bonus_credits > 0" class="text-green-400">
                + {{ pack.bonus_credits.toLocaleString() }} bonus!
              </span>
            </div>

            <button
              @click="buyCredits(pack.id)"
              :disabled="loadingAction === `credits-${pack.id}`"
              class="w-full py-3 bg-gold text-black rounded-lg font-medium hover:bg-gold/90 transition-colors disabled:opacity-50"
            >
              {{ loadingAction === `credits-${pack.id}` ? 'Processing...' : 'Buy Now' }}
            </button>
          </div>
        </div>
      </div>

      <div class="mt-8 text-center text-sm text-gray-500">
        Credits are billed once and never expire. Use them for any model beyond your subscription limit.
      </div>

      <!-- Coupon Redemption Section -->
      <div class="mt-12 max-w-md mx-auto">
        <div class="bg-surface rounded-xl p-6 border border-gray-700">
          <h3 class="text-lg font-semibold mb-4 text-center">Have a Coupon?</h3>

          <div class="flex gap-2">
            <input
              v-model="couponCode"
              type="text"
              placeholder="Enter coupon code"
              class="flex-1 px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:border-gold focus:outline-none uppercase"
              :disabled="loadingAction === 'coupon'"
              @keyup.enter="redeemCoupon"
            />
            <button
              @click="redeemCoupon"
              :disabled="!couponCode.trim() || loadingAction === 'coupon'"
              class="px-6 py-2 bg-gold text-black rounded-lg font-medium hover:bg-gold/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ loadingAction === 'coupon' ? 'Redeeming...' : 'Redeem' }}
            </button>
          </div>

          <!-- Coupon Result Message -->
          <div
            v-if="couponMessage"
            :class="[
              'mt-3 p-3 rounded-lg text-sm',
              couponMessage.success
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-red-500/20 text-red-400 border border-red-500/30'
            ]"
          >
            {{ couponMessage.text }}
          </div>
        </div>
      </div>
    </div>

    <!-- History Tab -->
    <div v-if="activeTab === 'history'" class="max-w-3xl mx-auto">
      <h2 class="text-2xl font-bold mb-6 text-center">Transaction History</h2>

      <div v-if="billing.loading" class="text-center py-8 text-gray-400">
        Loading transactions...
      </div>

      <div v-else-if="billing.transactions.length === 0" class="text-center py-8 text-gray-500">
        No transactions yet
      </div>

      <div v-else class="bg-surface rounded-xl border border-gray-700 overflow-hidden">
        <table class="w-full">
          <thead class="bg-gray-800/50">
            <tr>
              <th class="text-left px-4 py-3 text-sm font-medium text-gray-400">Date</th>
              <th class="text-left px-4 py-3 text-sm font-medium text-gray-400">Type</th>
              <th class="text-left px-4 py-3 text-sm font-medium text-gray-400">Description</th>
              <th class="text-right px-4 py-3 text-sm font-medium text-gray-400">Amount</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-700">
            <tr v-for="tx in billing.transactions" :key="tx.id" class="hover:bg-gray-800/30">
              <td class="px-4 py-3 text-sm text-gray-300">{{ formatDate(tx.created_at) }}</td>
              <td class="px-4 py-3">
                <span
                  :class="[
                    'text-xs px-2 py-1 rounded-full',
                    tx.transaction_type === 'purchase' ? 'bg-green-500/20 text-green-400' :
                    tx.transaction_type === 'usage' ? 'bg-blue-500/20 text-blue-400' :
                    tx.transaction_type === 'bonus' ? 'bg-gold/20 text-gold' :
                    'bg-gray-500/20 text-gray-400'
                  ]"
                >
                  {{ tx.transaction_type }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-300">{{ tx.description || '-' }}</td>
              <td
                class="px-4 py-3 text-sm text-right font-mono"
                :class="tx.amount_cents > 0 ? 'text-green-400' : 'text-red-400'"
              >
                {{ tx.amount_cents > 0 ? '+' : '' }}{{ (tx.amount_cents / 100).toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Not Authenticated Message -->
    <div v-if="!auth.isAuthenticated" class="mt-12 text-center">
      <div class="bg-surface rounded-xl p-8 border border-gray-700 max-w-md mx-auto">
        <h3 class="text-xl font-bold mb-2">Sign in to Subscribe</h3>
        <p class="text-gray-400 mb-4">Create an account to start your journey</p>
        <router-link to="/login" class="inline-block px-6 py-3 bg-gold text-black rounded-lg font-medium hover:bg-gold/90 transition-colors">
          Sign In
        </router-link>
      </div>
    </div>
  </div>
</template>

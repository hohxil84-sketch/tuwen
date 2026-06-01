<template>
  <div class="dashboard-page">
    <section class="top-row">
      <div class="welcome-card">
        <div class="welcome-greeting">
          <span class="welcome-emoji">👋</span>
          <div>
            <h2 class="welcome-title">{{ greeting }}，{{ displayName }}！</h2>
            <p class="welcome-sub">AI 图文广告助手已为您准备好，今天也要加油接单哦！</p>
          </div>
        </div>
      </div>

      <div class="stat-cards">
        <div v-for="stat in stats" :key="stat.label" class="stat-card">
          <div class="stat-icon" :class="`tone-${stat.tone}`">
            {{ stat.icon }}
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-helper">{{ stat.helper }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="quick-section">
      <h3 class="section-title">快捷功能</h3>
      <div class="quick-grid">
        <QuickEntryCard v-for="entry in quickEntries" :key="entry.title" :entry="entry" />
      </div>
    </section>

    <section class="bottom-row">
      <RecentOrders :orders="recentOrders" />
      <RecentGeneratedImages :images="generatedImages" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "@/stores/authStore";
import QuickEntryCard from "@/components/dashboard/QuickEntryCard.vue";
import RecentGeneratedImages from "@/components/dashboard/RecentGeneratedImages.vue";
import RecentOrders from "@/components/dashboard/RecentOrders.vue";
import {
  MOCK_IMAGES,
  MOCK_QUICK_ENTRIES,
  MOCK_RECENT_ORDERS,
  MOCK_STATS,
} from "./dashboardMock";

const auth = useAuthStore();

const stats = MOCK_STATS;
const quickEntries = MOCK_QUICK_ENTRIES;
const recentOrders = MOCK_RECENT_ORDERS;
const generatedImages = MOCK_IMAGES;

const displayName = computed(() => {
  if (auth.isLoggedIn && auth.userName) return auth.userName;
  return "张老板";
});

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "夜深了";
  if (hour < 9) return "早上好";
  if (hour < 12) return "上午好";
  if (hour < 14) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});
</script>

<style scoped>
.dashboard-page {
  width: 100%;
  margin: 0 auto;
  padding: 18px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-row {
  display: grid;
  grid-template-columns: minmax(420px, 1.3fr) minmax(400px, 1fr);
  gap: 16px;
}

.welcome-card {
  min-height: 194px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 12px;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 28%, rgba(47, 111, 237, 0.16), transparent 34%),
    linear-gradient(135deg, #10213b 0%, #142c50 52%, #18427f 100%);
  box-shadow: 0 20px 44px rgba(0, 0, 0, 0.16);
}

.welcome-greeting {
  height: 100%;
  min-height: 194px;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 0 36px;
}

.welcome-emoji {
  font-size: 42px;
  line-height: 1;
  filter: saturate(0.9);
}

.welcome-title {
  margin-bottom: 7px;
  color: var(--text-main);
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.welcome-sub {
  color: rgba(229, 237, 247, 0.74);
  font-size: 14px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 10px 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
  filter: saturate(0.82);
}

.tone-blue {
  background: rgba(47, 111, 237, 0.13);
}

.tone-green {
  background: rgba(34, 197, 94, 0.12);
}

.tone-purple {
  background: rgba(124, 110, 230, 0.12);
}

.tone-orange {
  background: rgba(216, 145, 40, 0.12);
}

.stat-body {
  min-width: 0;
}

.stat-value {
  color: var(--text-main);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
}

.stat-label {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.stat-helper {
  margin-top: 2px;
  color: var(--text-soft);
  font-size: 11px;
}

.section-title {
  margin-bottom: 12px;
  color: var(--text-main);
  font-size: 15px;
  font-weight: 600;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
}

.bottom-row {
  display: grid;
  grid-template-columns: minmax(480px, 1fr) minmax(480px, 1fr);
  gap: 16px;
}

@media (max-width: 1360px) {
  .bottom-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1180px) {
  .top-row {
    grid-template-columns: 1fr;
  }
}
</style>

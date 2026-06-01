<template>
  <header class="topbar">
    <div class="topbar-user">
      <div class="user-avatar">{{ userInitial }}</div>
      <div class="user-info">
        <span class="user-name">{{ displayName }}</span>
        <span class="user-plan">{{ planLabel }}</span>
      </div>
      <span class="topbar-divider"></span>
      <span class="topbar-status">
        <span class="status-dot"></span>
        在线
      </span>
      <span class="topbar-divider"></span>
      <span class="topbar-expiry">到期 {{ expiryDate }}</span>
    </div>

    <div class="topbar-actions">
      <button v-if="auth.isLoggedIn" class="topbar-btn" title="退出登录" @click="handleLogout">
        退出
      </button>
      <router-link v-else to="/login" class="topbar-btn">登录</router-link>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();
const expiryDate = "2025-12-31";

const displayName = computed(() => {
  if (auth.isLoggedIn && auth.userName) return auth.userName;
  return "张老板";
});

const userInitial = computed(() => displayName.value.charAt(0).toUpperCase());

const planLabel = computed(() => {
  if (auth.user?.plan_code) {
    const map: Record<string, string> = {
      standard: "标准版",
      pro: "高级版",
      enterprise: "企业版",
    };
    return map[auth.user.plan_code] || auth.user.plan_code;
  }
  return "高级版";
});

async function handleLogout(): Promise<void> {
  await auth.logout();
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 57px;
  padding: 0 28px;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1f4fbf, #5b3eb0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  filter: saturate(0.84);
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.user-name {
  color: var(--text-main);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}

.user-plan {
  color: var(--blue);
  font-size: 11px;
  line-height: 1.3;
}

.topbar-divider {
  width: 1px;
  height: 20px;
  background: var(--border-subtle);
}

.topbar-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 5px rgba(34, 197, 94, 0.36);
}

.topbar-expiry {
  color: var(--text-muted);
  font-size: 12px;
}

.topbar-actions {
  display: flex;
  align-items: center;
}

.topbar-btn {
  padding: 6px 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  text-decoration: none;
  transition: border-color 0.15s, color 0.15s;
}

.topbar-btn:hover {
  border-color: rgba(148, 163, 184, 0.34);
  color: var(--text-main);
}
</style>

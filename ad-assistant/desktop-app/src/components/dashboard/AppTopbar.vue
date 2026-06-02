<template>
  <header class="topbar" data-tauri-drag-region>
    <div class="topbar-user" data-tauri-drag-region>
      <div class="user-avatar">{{ userInitial }}</div>
      <div class="user-info" data-tauri-drag-region>
        <span class="user-name">{{ displayName }}</span>
        <span class="user-plan">{{ planLabel }}</span>
      </div>
      <span class="topbar-divider"></span>
      <span class="topbar-status" data-tauri-drag-region>
        <span class="status-dot"></span>
        在线
      </span>
      <span class="topbar-divider"></span>
      <span class="topbar-expiry" data-tauri-drag-region>到期 {{ expiryDate }}</span>
    </div>

    <div class="topbar-actions">
      <!-- 窗口控制按钮（仅在 Tauri 环境下显示） -->
      <div v-if="isTauri" class="win-controls">
        <button class="win-btn win-btn--min" title="最小化" @click="winMinimize">
          <svg width="12" height="12" viewBox="0 0 12 12"><rect y="5" width="12" height="1.5" fill="currentColor"/></svg>
        </button>
        <button class="win-btn win-btn--max" :title="isMaximized ? '还原' : '最大化'" @click="winToggleMax">
          <svg v-if="!isMaximized" width="12" height="12" viewBox="0 0 12 12"><rect x="1" y="1" width="10" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>
          <svg v-else width="12" height="12" viewBox="0 0 12 12"><rect x="2.5" y="0.5" width="8" height="8" rx="1" fill="none" stroke="currentColor" stroke-width="1.3"/><rect x="0.5" y="2.5" width="8" height="8" rx="1" fill="var(--bg-sidebar)" stroke="currentColor" stroke-width="1.3"/></svg>
        </button>
        <button class="win-btn win-btn--close" title="关闭" @click="winClose">
          <svg width="12" height="12" viewBox="0 0 12 12"><path d="M1 1l10 10M11 1L1 11" stroke="currentColor" stroke-width="1.5"/></svg>
        </button>
      </div>

      <button v-if="auth.isLoggedIn" class="topbar-btn" title="退出登录" @click="handleLogout">
        退出
      </button>
      <router-link v-else to="/login" class="topbar-btn">登录</router-link>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();
const expiryDate = "2025-12-31";

// Tauri 窗口控制（仅 Tauri 环境下可用，浏览器中安全降级）
const isTauri = ref(false);
const isMaximized = ref(false);

let tauriWindow: any = null;

onMounted(async () => {
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    tauriWindow = getCurrentWindow();
    isTauri.value = true;
    isMaximized.value = await tauriWindow.isMaximized();

    // 监听窗口最大化/还原事件，同步按钮图标
    const unlistenResize = await tauriWindow.onResized(async () => {
      isMaximized.value = await tauriWindow.isMaximized();
    });
    // 组件卸载时取消监听
    (window as any).__tauriWinUnlisten = unlistenResize;
  } catch {
    // 非 Tauri 环境（浏览器开发模式）：不显示窗口控制按钮
    isTauri.value = false;
  }
});

onBeforeUnmount(() => {
  if ((window as any).__tauriWinUnlisten) {
    (window as any).__tauriWinUnlisten();
    delete (window as any).__tauriWinUnlisten;
  }
});

async function winMinimize(): Promise<void> {
  try {
    await tauriWindow?.minimize();
  } catch { /* 静默降级 */ }
}

async function winToggleMax(): Promise<void> {
  try {
    await tauriWindow?.toggleMaximize();
  } catch { /* 静默降级 */ }
}

async function winClose(): Promise<void> {
  try {
    await tauriWindow?.close();
  } catch { /* 静默降级 */ }
}

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

/* 窗口控制按钮（Tauri frameless 模式下显示） */
.win-controls {
  display: flex;
  align-items: center;
  gap: 0;
  margin-right: 8px;
}

.win-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 28px;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.win-btn:hover {
  background: rgba(148, 163, 184, 0.12);
  color: var(--text-main);
}

.win-btn--close:hover {
  background: var(--red);
  color: #fff;
}
</style>

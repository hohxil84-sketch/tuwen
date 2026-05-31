<!-- Sprint-02 Task-05: Add basic navigation header -->
<template>
  <div id="app-shell">
    <header class="app-header">
      <nav class="nav-links">
        <router-link to="/" class="nav-logo">AI 图文助手</router-link>
        <router-link to="/ocr" class="nav-link">OCR 工作台</router-link>
        <router-link to="/history" class="nav-link">历史记录</router-link>
      </nav>
      <div class="nav-auth">
        <template v-if="auth.isLoggedIn">
          <span class="nav-user">{{ auth.userName }}</span>
          <button class="btn btn-sm btn-outline" @click="handleLogout">退出</button>
        </template>
        <router-link v-else to="/login" class="nav-link">登录</router-link>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();

async function handleLogout(): Promise<void> {
  await auth.logout();
}
</script>

<style>
/* ---- Global reset (minimal) ---- */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial,
    "PingFang SC", "Microsoft YaHei", sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

/* ---- App shell ---- */
#app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ---- Header ---- */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 52px;
  background-color: #fff;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-logo {
  font-weight: 700;
  font-size: 16px;
  color: #1e40af;
  text-decoration: none;
  margin-right: 8px;
}

.nav-link {
  font-size: 13px;
  color: #666;
  text-decoration: none;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 0.15s, background-color 0.15s;
}

.nav-link:hover {
  color: #1e40af;
  background-color: #eff6ff;
}

.nav-link.router-link-active {
  color: #3b82f6;
  font-weight: 500;
}

.nav-auth {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-user {
  font-size: 13px;
  color: #666;
}

/* ---- Main ---- */
.app-main {
  flex: 1;
}

/* ---- Shared button helpers ---- */
.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.btn-outline {
  background-color: transparent;
  border: 1px solid #d1d5db;
  color: #666;
}

.btn-outline:hover {
  border-color: #ef4444;
  color: #ef4444;
}
</style>

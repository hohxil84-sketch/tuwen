<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-icon">🖼️</span>
      <span class="brand-text">AI 图文广告助手</span>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-group">
        <router-link to="/" class="nav-item" :class="{ active: isActive('/') }">
          <span class="nav-icon">📊</span>
          <span class="nav-label">工作台</span>
        </router-link>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">核心功能</div>
        <div
          v-for="item in coreFeatures"
          :key="item.label"
          class="nav-item"
          :class="{ active: isActive(item.route), disabled: item.disabled }"
          @click="navTo(item)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.disabled" class="nav-badge">即将开放</span>
        </div>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">辅助功能</div>
        <div v-for="item in auxFeatures" :key="item.label" class="nav-item disabled">
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
          <span class="nav-badge">即将开放</span>
        </div>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">订单管理</div>
        <router-link to="/history" class="nav-item" :class="{ active: isActive('/history') }">
          <span class="nav-icon">📋</span>
          <span class="nav-label">我的订单</span>
        </router-link>
        <div class="nav-item disabled">
          <span class="nav-icon">👥</span>
          <span class="nav-label">客户管理</span>
          <span class="nav-badge">即将开放</span>
        </div>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">系统设置</div>
        <div class="nav-item disabled">
          <span class="nav-icon">⚙️</span>
          <span class="nav-label">软件设置</span>
          <span class="nav-badge">即将开放</span>
        </div>
        <div class="nav-item disabled">
          <span class="nav-icon">🔄</span>
          <span class="nav-label">更新检查</span>
          <span class="nav-badge">即将开放</span>
        </div>
        <router-link to="/history" class="nav-item" :class="{ active: isActive('/history') }">
          <span class="nav-icon">📄</span>
          <span class="nav-label">使用日志</span>
        </router-link>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-version">v1.0.0</div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";

interface NavFeature {
  label: string;
  icon: string;
  route: string;
  disabled: boolean;
}

const route = useRoute();
const router = useRouter();

const coreFeatures: NavFeature[] = [
  { label: "AI 效果图生成", icon: "🎨", route: "/", disabled: true },
  { label: "AI 文案生成", icon: "✍️", route: "/", disabled: true },
  { label: "图片改尺寸", icon: "📐", route: "/", disabled: true },
  { label: "图片转矢量 SVG", icon: "🔷", route: "/", disabled: true },
  { label: "印刷检查", icon: "✅", route: "/", disabled: true },
  { label: "OCR 文字识别", icon: "📝", route: "/ocr", disabled: false },
];

const auxFeatures: NavFeature[] = [
  { label: "智能抠图", icon: "✂️", route: "/", disabled: true },
  { label: "AI 证件照", icon: "📷", route: "/", disabled: true },
  { label: "批量处理", icon: "📦", route: "/", disabled: true },
  { label: "拼版助手", icon: "📑", route: "/", disabled: true },
  { label: "素材库", icon: "🗂️", route: "/", disabled: true },
  { label: "模板中心", icon: "🧾", route: "/", disabled: true },
];

function isActive(path: string): boolean {
  return route.path === path;
}

function navTo(item: NavFeature): void {
  if (item.disabled) return;
  router.push(item.route);
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100%;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 57px;
  padding: 0 22px;
  border-bottom: 1px solid var(--border-subtle);
}

.brand-icon {
  font-size: 22px;
  line-height: 1;
}

.brand-text {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  overflow: hidden;
}

.nav-group {
  margin-bottom: 11px;
}

.nav-group-title {
  padding: 7px 10px 5px;
  color: var(--text-soft);
  font-size: 12px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 35px;
  padding: 0 12px;
  border-radius: 7px;
  color: var(--text-muted);
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
}

.nav-item + .nav-item {
  margin-top: 2px;
}

.nav-item:hover:not(.disabled) {
  background: rgba(47, 111, 237, 0.08);
  color: var(--text-main);
}

.nav-item.active {
  background: linear-gradient(135deg, #16315a, #1d55b1);
  color: #fff;
}

.nav-item.disabled {
  cursor: not-allowed;
  opacity: 0.46;
}

.nav-icon {
  width: 22px;
  flex-shrink: 0;
  text-align: center;
  font-size: 16px;
  line-height: 1;
  filter: saturate(0.82);
}

.nav-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-badge {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.11);
  color: rgba(148, 163, 184, 0.62);
  font-size: 10px;
  white-space: nowrap;
}

.sidebar-footer {
  height: 40px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  border-top: 1px solid var(--border-subtle);
}

.sidebar-version {
  color: var(--text-soft);
  font-size: 11px;
}
</style>

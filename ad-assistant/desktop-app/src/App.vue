<template>
  <div id="app-shell" ref="viewportRef">
    <div class="app-scale-stage" :style="stageStyle">
      <div class="app-layout">
        <AppSidebar />
        <div class="app-right">
          <AppTopbar />
          <main class="app-main">
            <router-view />
          </main>
          <footer class="app-footer">
            <span class="footer-left">
              <span class="footer-dot"></span>
              已连接到服务器（mock）
            </span>
            <span class="footer-mid">版本：1.0.0</span>
            <span class="footer-right">
              <a href="#" class="footer-link" @click.prevent="noop">检查更新</a>
            </span>
          </footer>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import AppSidebar from "@/components/dashboard/AppSidebar.vue";
import AppTopbar from "@/components/dashboard/AppTopbar.vue";

const DESIGN_WIDTH = 1366;

const viewportRef = ref<HTMLElement | null>(null);
const viewportWidth = ref(DESIGN_WIDTH);

const scale = computed(() => {
  return Math.min(1, viewportWidth.value / DESIGN_WIDTH);
});

const stageStyle = computed(() => ({
  width: `${DESIGN_WIDTH}px`,
  transform: `scale(${scale.value})`,
}));

function updateViewportSize(): void {
  const viewport = viewportRef.value;
  viewportWidth.value = viewport?.clientWidth || window.innerWidth || DESIGN_WIDTH;
}

function noop(): void {
  // MOCK: check for updates is not implemented yet.
}

onMounted(() => {
  updateViewportSize();
  window.addEventListener("resize", updateViewportSize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateViewportSize);
});
</script>

<style>
:root {
  --bg-app: #07111f;
  --bg-sidebar: #081322;
  --bg-panel: #101d31;
  --bg-panel-soft: #13233a;
  --border-subtle: rgba(148, 163, 184, 0.14);
  --border-active: rgba(47, 111, 237, 0.45);
  --text-main: #e5edf7;
  --text-muted: #94a3b8;
  --text-soft: #64748b;
  --blue: #2f6fed;
  --blue-strong: #1f4fbf;
  --blue-soft: rgba(47, 111, 237, 0.16);
  --green: #22c55e;
  --orange: #d89128;
  --red: #ef4444;
  --purple: #7c6ee6;
  --cyan: #25a6b8;
  --card-bg: linear-gradient(180deg, rgba(19, 35, 58, 0.96), rgba(13, 27, 45, 0.96));
  --panel-highlight: linear-gradient(135deg, #132b4d 0%, #183b73 52%, #1d4f9a 100%);
}

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
  min-width: 0;
  overflow: hidden;
}

body {
  font-family:
    "Microsoft YaHei",
    "PingFang SC",
    "Noto Sans SC",
    system-ui,
    sans-serif;
  background-color: var(--bg-app);
  color: var(--text-muted);
}

body,
#app-shell,
.app-layout,
.dashboard-card,
.nav-item,
button {
  user-select: none;
  -webkit-user-select: none;
}

input,
textarea,
[contenteditable="true"],
.copyable,
.ocr-result {
  user-select: text;
  -webkit-user-select: text;
}

img,
svg {
  user-drag: none;
  -webkit-user-drag: none;
}

* {
  scrollbar-width: thin;
  scrollbar-color: rgba(100, 116, 139, 0.36) transparent;
}

*::-webkit-scrollbar {
  width: 7px;
  height: 7px;
}

*::-webkit-scrollbar-track {
  background: transparent;
}

*::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.34);
  border-radius: 999px;
}

#app-shell {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-app);
}

.app-scale-stage {
  transform-origin: top left;
  overflow: hidden;
}

.app-layout {
  display: flex;
  width: 1366px;
  height: 100vh;
  overflow: hidden;
}

.app-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  overflow: hidden;
}

.app-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--bg-app);
}

.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 28px;
  background: var(--bg-sidebar);
  border-top: 1px solid var(--border-subtle);
  font-size: 12px;
  flex-shrink: 0;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
}

.footer-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 4px rgba(34, 197, 94, 0.28);
}

.footer-mid,
.footer-right {
  color: var(--text-soft);
}

.footer-link {
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}

.footer-link:hover {
  color: var(--blue);
}
</style>

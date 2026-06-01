<template>
  <div class="recent-images">
    <div class="card-header">
      <h3 class="card-title">最近生成效果图</h3>
      <span class="card-link" @click="noop">查看全部 →</span>
    </div>

    <div class="image-grid">
      <div v-for="img in images" :key="img.title" class="image-card">
        <div class="image-preview" :style="{ background: img.gradient }">
          <span class="image-placeholder-text">{{ img.title }}</span>
        </div>
        <div class="image-info">
          <div class="image-title">{{ img.title }}</div>
          <div class="image-time">{{ img.time }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GeneratedImage } from "@/pages/dashboardMock";

defineProps<{ images: GeneratedImage[] }>();

function noop(): void {
  // MOCK: view all generated images is not implemented yet.
}
</script>

<style scoped>
.recent-images {
  min-height: 360px;
  overflow: hidden;
  background: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.14);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 22px;
}

.card-title {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 600;
}

.card-link {
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
}

.card-link:hover {
  color: var(--blue);
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 14px;
  padding: 0 22px 20px;
}

.image-card {
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
}

.image-preview {
  position: relative;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: saturate(0.78);
}

.image-preview::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.06), transparent),
    linear-gradient(135deg, rgba(47, 111, 237, 0.2), rgba(15, 23, 42, 0.78));
  pointer-events: none;
}

.image-placeholder-text {
  position: relative;
  z-index: 1;
  padding: 8px;
  color: rgba(229, 237, 247, 0.72);
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

.image-info {
  padding: 9px 12px;
}

.image-title {
  overflow: hidden;
  margin-bottom: 3px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-time {
  color: var(--text-soft);
  font-size: 11px;
}
</style>

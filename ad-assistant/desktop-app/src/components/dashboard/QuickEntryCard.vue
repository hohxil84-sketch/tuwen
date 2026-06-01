<template>
  <div class="quick-entry-card" :class="{ disabled: entry.disabled }" @click="handleClick">
    <div class="entry-icon" :class="`tone-${entry.tone}`">
      {{ entry.icon }}
    </div>
    <div class="entry-body">
      <div class="entry-title">{{ entry.title }}</div>
      <div class="entry-desc">{{ entry.description }}</div>
    </div>
    <div v-if="entry.disabled" class="entry-badge">即将开放</div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import type { QuickEntry } from "@/pages/dashboardMock";

const props = defineProps<{ entry: QuickEntry }>();
const router = useRouter();

function handleClick(): void {
  if (props.entry.disabled) return;
  if (props.entry.route) router.push(props.entry.route);
}
</script>

<style scoped>
.quick-entry-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  height: 97px;
  padding: 18px 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.14);
  cursor: pointer;
  transition: transform 0.18s, border-color 0.18s;
}

.quick-entry-card:hover:not(.disabled) {
  transform: translateY(-2px);
  border-color: rgba(47, 111, 237, 0.26);
}

.quick-entry-card.disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.entry-icon {
  width: 56px;
  height: 56px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 24px;
  filter: saturate(0.82);
}

.entry-icon.tone-blue {
  background: rgba(47, 111, 237, 0.12);
}

.entry-icon.tone-orange {
  background: rgba(216, 145, 40, 0.12);
}

.entry-icon.tone-cyan {
  background: rgba(37, 166, 184, 0.12);
}

.entry-icon.tone-green {
  background: rgba(34, 197, 94, 0.12);
}

.entry-icon.tone-purple {
  background: rgba(124, 110, 230, 0.12);
}

.entry-body {
  min-width: 0;
}

.entry-title {
  margin-bottom: 6px;
  color: var(--text-main);
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.entry-desc {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entry-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.11);
  color: rgba(148, 163, 184, 0.58);
  font-size: 10px;
}
</style>

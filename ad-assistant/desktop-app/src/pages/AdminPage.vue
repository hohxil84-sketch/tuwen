<template>
  <div class="admin-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h2 class="page-title">管理后台</h2>
      <p class="page-desc">只读数据面板</p>
    </header>

    <!-- Permission denied -->
    <div v-if="forbidden" class="empty-state">
      <p>无管理权限。当前账户不在管理员白名单中。</p>
      <button class="btn-primary" @click="goBack">返回工作台</button>
    </div>

    <!-- Admin content -->
    <div v-else class="admin-content">
      <!-- Tab bar -->
      <nav class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </nav>

      <!-- Loading -->
      <div v-if="loading" class="loading-msg">加载中...</div>

      <!-- Error -->
      <div v-else-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

      <!-- Table -->
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="col in activeColumns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="rows.length === 0">
              <td :colspan="activeColumns.length" class="empty-cell">
                暂无数据
              </td>
            </tr>
            <tr v-for="(row, ri) in rows" :key="ri">
              <td v-for="col in activeColumns" :key="col">
                {{ formatCell(row, col) }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="pagination">
          <button :disabled="offset === 0" @click="prevPage">上一页</button>
          <span class="page-info">
            {{ offset + 1 }}–{{ offset + rows.length }} / {{ total }}
          </span>
          <button :disabled="offset + rows.length >= total" @click="nextPage">
            下一页
          </button>
          <span class="page-limit">每页 {{ limit }} 条</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  adminListUsers,
  adminListOrders,
  adminListCreditAccounts,
  adminListProviderLogs,
  adminListUsageEvents,
  sanitizeApiError,
  type AdminPaginatedData,
  type AdminUserItem,
  type AdminOrderItem,
  type AdminCreditAccountItem,
  type AdminProviderLogItem,
  type AdminUsageEventItem,
  type CloudAPIErrorDetail,
} from "@/services/cloudApi";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TabKey = "users" | "orders" | "credit-accounts" | "provider-logs" | "usage-events";

interface TabDef {
  key: TabKey;
  label: string;
  columns: string[];
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AdminRow = Record<string, any>;

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

const tabs: TabDef[] = [
  {
    key: "users",
    label: "用户",
    columns: ["account", "role", "plan_code", "status", "created_at"],
  },
  {
    key: "orders",
    label: "订单",
    columns: ["user_id", "plan_code", "amount_cny", "credits", "status", "created_at"],
  },
  {
    key: "credit-accounts",
    label: "积分账户",
    columns: ["user_id", "plan_code", "balance", "monthly_grant", "status"],
  },
  {
    key: "provider-logs",
    label: "Provider 日志",
    columns: ["user_id", "provider", "model", "feature", "status", "credits_charged", "created_at"],
  },
  {
    key: "usage-events",
    label: "使用事件",
    columns: ["user_id", "event_type", "feature", "created_at"],
  },
];

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const router = useRouter();
const activeTab = ref<TabKey>("users");
const loading = ref(false);
const errorMsg = ref<string | null>(null);
const forbidden = ref(false);

const limit = 20;
const offset = ref(0);
const total = ref(0);
const rows = ref<AdminRow[]>([]);

const activeTabDef = computed(() => tabs.find((t) => t.key === activeTab.value)!);
const activeColumns = computed(() => activeTabDef.value.columns);

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

const fetchers: Record<TabKey, () => Promise<AdminPaginatedData<unknown>>> = {
  "users": () => adminListUsers(limit, offset.value),
  "orders": () => adminListOrders(limit, offset.value),
  "credit-accounts": () => adminListCreditAccounts(limit, offset.value),
  "provider-logs": () => adminListProviderLogs(limit, offset.value),
  "usage-events": () => adminListUsageEvents(limit, offset.value),
};

async function fetchTab(): Promise<void> {
  loading.value = true;
  errorMsg.value = null;
  forbidden.value = false;
  try {
    const data = await fetchers[activeTab.value]();
    rows.value = data.items as AdminRow[];
    total.value = data.total;
  } catch (err: unknown) {
    const apiErr = err as CloudAPIErrorDetail;
    if (apiErr.code === "FORBIDDEN") {
      forbidden.value = true;
    } else {
      errorMsg.value = sanitizeApiError(apiErr);
    }
    rows.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function switchTab(key: TabKey): void {
  activeTab.value = key;
  offset.value = 0;
  fetchTab();
}

function prevPage(): void {
  offset.value = Math.max(0, offset.value - limit);
  fetchTab();
}

function nextPage(): void {
  offset.value = offset.value + limit;
  fetchTab();
}

// Initial load
fetchTab();

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function goBack(): void {
  router.push("/");
}

// ---------------------------------------------------------------------------
// Cell formatting
// ---------------------------------------------------------------------------

function formatCell(row: AdminRow, col: string): string {
  const v = row[col];
  if (v === null || v === undefined) return "—";
  if (typeof v === "string" && v.length > 40) return v.slice(0, 40) + "…";
  return String(v);
}
</script>

<style scoped>
.admin-page {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 24px 40px;
}

.page-header {
  margin-bottom: 16px;
}

.back-btn {
  display: inline-block;
  margin-bottom: 8px;
  padding: 4px 0;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
}

.back-btn:hover {
  color: var(--blue);
}

.page-title {
  margin-bottom: 4px;
  color: var(--text-main);
  font-size: 22px;
  font-weight: 700;
}

.page-desc {
  color: var(--text-muted);
  font-size: 13px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 60px 20px;
  color: var(--text-muted);
  text-align: center;
}

.btn-primary {
  padding: 10px 28px;
  background: var(--blue);
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.admin-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Tab bar */
.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-subtle);
  overflow-x: auto;
}

.tab-btn {
  padding: 8px 18px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;
}

.tab-btn:hover {
  color: var(--text-main);
}

.tab-btn.active {
  color: var(--blue);
  border-bottom-color: var(--blue);
}

/* States */
.loading-msg {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.error-msg {
  padding: 10px 14px;
  background: rgba(224, 79, 95, 0.1);
  border: 1px solid rgba(224, 79, 95, 0.2);
  border-radius: 6px;
  color: #e04f5f;
  font-size: 13px;
}

/* Table */
.table-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th {
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
}

.data-table td {
  padding: 7px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  color: var(--text-main);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-cell {
  text-align: center;
  color: var(--text-muted);
  padding: 30px 10px;
}

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.pagination button {
  padding: 5px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  color: var(--text-main);
  cursor: pointer;
  font-size: 12px;
}

.pagination button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.06);
}

.page-info {
  color: var(--text-muted);
  font-size: 12px;
  min-width: 80px;
  text-align: center;
}

.page-limit {
  color: var(--text-muted);
  font-size: 11px;
}
</style>

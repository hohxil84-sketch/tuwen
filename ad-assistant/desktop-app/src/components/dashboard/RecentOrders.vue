<template>
  <div class="recent-orders">
    <div class="card-header">
      <h3 class="card-title">最近订单</h3>
      <span class="card-link" @click="noop">查看全部 →</span>
    </div>

    <div class="table-wrap">
      <table class="orders-table">
        <thead>
          <tr>
            <th>订单号</th>
            <th>客户名称</th>
            <th>项目名称</th>
            <th>状态</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.orderNo">
            <td class="col-order-no">{{ order.orderNo }}</td>
            <td>{{ order.customerName }}</td>
            <td>{{ order.projectName }}</td>
            <td>
              <span class="status-tag" :class="`status-${statusClass(order.status)}`">
                {{ order.status }}
              </span>
            </td>
            <td class="col-time">{{ order.updatedAt }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RecentOrder } from "@/pages/dashboardMock";

defineProps<{ orders: RecentOrder[] }>();

function statusClass(status: RecentOrder["status"]): string {
  const map: Record<RecentOrder["status"], string> = {
    已完成: "done",
    进行中: "progress",
    待确认: "pending",
  };
  return map[status];
}

function noop(): void {
  // MOCK: view all orders is not implemented yet.
}
</script>

<style scoped>
.recent-orders {
  min-height: 296px;
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

.table-wrap {
  padding: 0 22px 18px;
  overflow: hidden;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;
}

.orders-table th {
  padding: 11px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  color: var(--text-soft);
  font-size: 11px;
  font-weight: 500;
  text-align: left;
  white-space: nowrap;
}

.orders-table td {
  overflow: hidden;
  padding: 9px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.06);
  color: var(--text-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.orders-table th:nth-child(1),
.orders-table td:nth-child(1) {
  width: 126px;
}

.orders-table th:nth-child(2),
.orders-table td:nth-child(2) {
  width: 136px;
}

.orders-table th:nth-child(3),
.orders-table td:nth-child(3) {
  width: 108px;
}

.orders-table th:nth-child(4),
.orders-table td:nth-child(4) {
  width: 94px;
}

.col-order-no {
  font-family: "Consolas", "Menlo", monospace;
  font-size: 12px;
}

.col-time {
  color: var(--text-soft);
  font-size: 12px;
}

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-done {
  background: rgba(34, 197, 94, 0.14);
  color: var(--green);
}

.status-progress {
  background: rgba(47, 111, 237, 0.14);
  color: var(--blue);
}

.status-pending {
  background: rgba(216, 145, 40, 0.14);
  color: var(--orange);
}
</style>

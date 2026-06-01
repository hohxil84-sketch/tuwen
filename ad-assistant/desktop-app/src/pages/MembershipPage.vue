<template>
  <div class="membership-page">
    <!-- Loading skeleton -->
    <div v-if="isLoading && !hasData" class="loading-area" aria-busy="true">
      <div v-for="i in 4" :key="i" class="skeleton-card">
        <div class="skeleton-line w-60"></div>
        <div class="skeleton-line w-40"></div>
        <div class="skeleton-line w-80"></div>
      </div>
    </div>

    <template v-else>
      <!-- Current plan banner -->
      <section class="current-plan-banner" :class="`plan-${currentPlanCode}`">
        <div class="banner-left">
          <h2 class="banner-plan-name">{{ currentPlanLabel }}</h2>
          <p class="banner-plan-desc">
            当前套餐 · {{ currentPlanLabel }}
          </p>
        </div>
        <div class="banner-right">
          <div class="banner-stat">
            <span class="banner-stat-value">{{ creditBalance }}</span>
            <span class="banner-stat-label">剩余算力额度</span>
          </div>
          <div class="banner-stat">
            <span class="banner-stat-value">{{ creditsUnit }}</span>
            <span class="banner-stat-label">折算人民币</span>
          </div>
        </div>
      </section>

      <!-- Plan comparison -->
      <section class="plans-section">
        <h3 class="section-title">选择适合您的套餐</h3>
        <div class="plans-grid">
          <div
            v-for="plan in plans"
            :key="plan.code"
            class="plan-card"
            :class="{ 'plan-current': plan.code === currentPlanCode, 'plan-popular': plan.code === 'expert' }"
          >
            <div v-if="plan.code === 'expert'" class="plan-popular-badge">🔥 最受欢迎</div>
            <h4 class="plan-card-name">{{ plan.name }}</h4>
            <div class="plan-card-price">
              <span class="plan-price-num">{{ plan.price_cny }}</span>
              <span class="plan-price-unit">元/月</span>
            </div>
            <p class="plan-credits-info">每月赠送 {{ plan.monthly_credits }} 算力额度</p>
            <div class="plan-divider"></div>
            <ul class="plan-features">
              <li v-for="feat in plan.features" :key="feat" class="plan-feature-item">
                <span class="plan-feature-check" aria-hidden="true">✓</span>
                {{ feat }}
              </li>
            </ul>
            <button
              class="plan-btn"
              :class="{
                'plan-btn-current': plan.code === currentPlanCode,
                'plan-btn-primary': plan.code !== currentPlanCode,
              }"
              :disabled="plan.code === currentPlanCode || isRecharging"
              @click="plan.code !== currentPlanCode && confirmRecharge(plan)"
            >
              {{ plan.code === currentPlanCode ? '当前套餐' : isRecharging && pendingPlan === plan.code ? '处理中...' : `升级到 ${plan.name}` }}
            </button>
          </div>
        </div>
      </section>

      <!-- Order history -->
      <section class="orders-section">
        <h3 class="section-title">充值记录</h3>
        <div v-if="orders.length === 0 && !ordersLoading" class="empty-state">
          <span class="empty-icon" role="img" aria-label="暂无记录">📭</span>
          <p>暂无充值记录</p>
        </div>
        <div v-else class="orders-table-wrap">
          <table class="orders-table">
            <thead>
              <tr>
                <th>订单编号</th>
                <th>金额</th>
                <th>获得积分</th>
                <th>支付方式</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>完成时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="order-id">{{ String(order.id).slice(0, 8) }}...</td>
                <td class="order-amount">¥{{ order.amount_cny }}</td>
                <td class="order-credits">{{ order.credits }}</td>
                <td>{{ paymentLabel(order.payment_method) }}</td>
                <td>
                  <span class="order-status" :class="`status-${order.status}`">
                    {{ statusLabel(order.status) }}
                  </span>
                </td>
                <td class="order-time">{{ formatTime(order.created_at) }}</td>
                <td class="order-time">{{ formatTime(order.completed_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- Recharge confirmation dialog -->
    <Teleport to="body">
      <div
        v-if="showRechargeConfirm"
        class="modal-overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="recharge-modal-title"
        @click.self="cancelRecharge"
        @keydown.escape="cancelRecharge"
      >
        <div class="modal-content">
          <h3 id="recharge-modal-title" class="modal-title">确认充值</h3>
          <div class="modal-body">
            <p class="modal-plan">{{ selectedPlan?.name }}</p>
            <p class="modal-price">¥{{ selectedPlan?.price_cny }} / 月</p>
            <p class="modal-credits">获赠 {{ selectedPlan?.monthly_credits }} 算力额度</p>
            <p v-if="rechargeError" class="modal-error">{{ rechargeError }}</p>
          </div>
          <div class="modal-actions">
            <button class="modal-btn modal-btn-cancel" :disabled="isRecharging" @click="cancelRecharge">
              取消
            </button>
            <button class="modal-btn modal-btn-confirm" :disabled="isRecharging" @click="executeRecharge">
              {{ isRecharging ? '处理中...' : '确认下单' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  listPlans,
  rechargeCredits,
  listOrders,
  dashboardSummary,
  type PlanData,
  type OrderItemData,
} from "@/services/cloudApi";
import { useAuthStore } from "@/stores/authStore";
import type { CloudAPIErrorDetail } from "@/services/cloudApi";

const auth = useAuthStore();

// State
const plans = ref<PlanData[]>([]);
const orders = ref<OrderItemData[]>([]);
const isLoading = ref(true);
const ordersLoading = ref(false);
const isRecharging = ref(false);
const showRechargeConfirm = ref(false);
const selectedPlan = ref<PlanData | null>(null);
const pendingPlan = ref<string | null>(null);
const rechargeError = ref<string | null>(null);
const creditBalance = ref(0);

const hasData = computed(() => plans.value.length > 0);

const currentPlanCode = computed(() => auth.user?.plan_code || "standard");

const currentPlanLabel = computed(() => {
  const map: Record<string, string> = {
    standard: "标准版",
    expert: "专家版",
    enterprise: "企业版",
  };
  return map[currentPlanCode.value] || currentPlanCode.value;
});

const creditsUnit = computed(() => `${(creditBalance.value / 100).toFixed(2)} 元`);

function paymentLabel(method: string): string {
  const map: Record<string, string> = {
    simulated: "模拟支付",
    alipay: "支付宝",
    wechat_pay: "微信支付",
    stripe: "Stripe",
    manual: "手动充值",
    offline: "线下汇款",
  };
  return map[method] || method;
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    completed: "已完成",
    pending: "处理中",
    cancelled: "已取消",
    refunded: "已退款",
  };
  return map[status] || status;
}

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function confirmRecharge(plan: PlanData): void {
  selectedPlan.value = plan;
  pendingPlan.value = plan.code;
  rechargeError.value = null;
  showRechargeConfirm.value = true;
}

function cancelRecharge(): void {
  showRechargeConfirm.value = false;
  pendingPlan.value = null;
  selectedPlan.value = null;
  rechargeError.value = null;
}

async function executeRecharge(): Promise<void> {
  if (!selectedPlan.value || isRecharging.value) return;
  isRecharging.value = true;
  rechargeError.value = null;

  try {
    const result = await rechargeCredits(selectedPlan.value.code);
    creditBalance.value = result.new_balance;
    showRechargeConfirm.value = false;
    selectedPlan.value = null;
    pendingPlan.value = null;

    // If plan was upgraded, update the in-memory user state so the
    // UI reflects the new plan immediately (JWT still carries the old
    // plan_code until next login, but DB and UI are consistent).
    if (result.plan_changed && result.plan_code) {
      auth.updatePlanCode(result.plan_code);
    }

    // Refresh orders
    await loadOrders();
  } catch (err: unknown) {
    const apiErr = err as CloudAPIErrorDetail;
    rechargeError.value = apiErr?.message || "充值失败，请稍后再试。";
  } finally {
    isRecharging.value = false;
  }
}

async function loadBalance(): Promise<void> {
  try {
    const summary = await dashboardSummary();
    creditBalance.value = summary.credit_balance;
  } catch {
    // Balance stays at 0 on failure
  }
}

async function loadPlans(): Promise<void> {
  try {
    const data = await listPlans();
    plans.value = data.items;
  } catch {
    plans.value = [];
  }
}

async function loadOrders(): Promise<void> {
  ordersLoading.value = true;
  try {
    const data = await listOrders(20, 0);
    orders.value = data.items;
  } catch {
    orders.value = [];
  } finally {
    ordersLoading.value = false;
  }
}

onMounted(async () => {
  isLoading.value = true;
  await Promise.all([loadPlans(), loadOrders(), loadBalance()]);
  isLoading.value = false;
});
</script>

<style scoped>
.membership-page {
  padding: 28px 32px;
  max-width: 1100px;
}

/* ---- Loading skeleton ---- */
.loading-area {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.skeleton-card {
  flex: 1;
  min-width: 200px;
  padding: 24px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
}

/* ---- Current plan banner ---- */
.current-plan-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px 32px;
  border-radius: 14px;
  margin-bottom: 36px;
  color: #fff;
  background: linear-gradient(135deg, #1a3a6b, #1e4990);
}

.current-plan-banner.plan-expert {
  background: linear-gradient(135deg, #3d1a6b, #6b1e90);
}

.current-plan-banner.plan-enterprise {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
}

.banner-left {
  flex: 1;
}

.banner-plan-name {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 6px;
}

.banner-plan-desc {
  font-size: 14px;
  opacity: 0.8;
  margin: 0;
}

.banner-right {
  display: flex;
  gap: 40px;
}

.banner-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.banner-stat-value {
  font-size: 28px;
  font-weight: 700;
}

.banner-stat-label {
  font-size: 13px;
  opacity: 0.75;
  margin-top: 4px;
}

/* ---- Section ---- */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0 0 20px;
}

/* ---- Plan cards ---- */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 44px;
}

.plan-card {
  position: relative;
  padding: 28px 24px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.plan-card:hover {
  border-color: rgba(47, 111, 237, 0.3);
}

.plan-card.plan-current {
  border-color: var(--blue);
  box-shadow: 0 0 0 1px rgba(47, 111, 237, 0.2);
}

.plan-card.plan-popular {
  border-color: rgba(255, 152, 0, 0.3);
}

.plan-popular-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 16px;
  border-radius: 20px;
  background: linear-gradient(135deg, #ff9800, #f57c00);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.plan-card-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 12px;
  text-align: center;
}

.plan-card-price {
  text-align: center;
  margin-bottom: 8px;
}

.plan-price-num {
  font-size: 36px;
  font-weight: 700;
  color: var(--blue);
}

.plan-price-unit {
  font-size: 14px;
  color: var(--text-muted);
  margin-left: 2px;
}

.plan-credits-info {
  text-align: center;
  font-size: 13px;
  color: var(--text-soft);
  margin: 0 0 16px;
}

.plan-divider {
  height: 1px;
  background: var(--border-subtle);
  margin-bottom: 16px;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 20px;
  flex: 1;
}

.plan-feature-item {
  padding: 6px 0;
  font-size: 13px;
  color: var(--text-muted);
}

.plan-feature-check {
  color: var(--green);
  font-weight: 700;
  margin-right: 8px;
}

.plan-btn {
  width: 100%;
  padding: 12px 0;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
}

.plan-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.plan-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.plan-btn-current {
  background: var(--bg-muted);
  color: var(--text-muted);
}

.plan-btn-primary {
  background: linear-gradient(135deg, var(--blue), var(--blue-strong));
  color: #fff;
}

/* ---- Orders table ---- */
.orders-table-wrap {
  overflow-x: auto;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.orders-table th,
.orders-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-muted);
}

.orders-table th {
  font-weight: 600;
  color: var(--text-soft);
  font-size: 12px;
  text-transform: uppercase;
}

.order-id {
  font-family: monospace;
  font-size: 12px;
}

.order-amount {
  font-weight: 600;
  color: var(--text-main);
}

.order-credits {
  font-weight: 600;
  color: var(--green);
}

.order-status {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-completed {
  background: rgba(34, 197, 94, 0.12);
  color: var(--green);
}

.status-pending {
  background: rgba(255, 152, 0, 0.12);
  color: var(--orange);
}

.order-time {
  font-size: 12px;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 40px;
  display: block;
  margin-bottom: 12px;
}

/* ---- Modal ---- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 28px 32px;
  min-width: 380px;
  max-width: 480px;
}

.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 20px;
}

.modal-body {
  margin-bottom: 24px;
}

.modal-plan {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0 0 6px;
}

.modal-price {
  font-size: 28px;
  font-weight: 700;
  color: var(--blue);
  margin: 0 0 6px;
}

.modal-credits {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.modal-error {
  color: var(--red);
  font-size: 13px;
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(239, 83, 80, 0.08);
  border-radius: 8px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.modal-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.modal-btn-cancel {
  background: var(--bg-muted);
  color: var(--text-muted);
}

.modal-btn-confirm {
  background: linear-gradient(135deg, var(--blue), var(--blue-strong));
  color: #fff;
}
</style>

/**
 * Vue Router — Sprint-03 Task-04 Dashboard UI.
 *
 * Pages:
 * - DashboardPage (new — /)
 * - LoginPage
 * - OcrPage
 * - HistoryPage
 *
 * Sprint-02 Task-05: No router-level auth guard was added. Each page
 * checks auth state internally via the Pinia authStore and shows
 * a login prompt when the user is not authenticated.
 */
import { createRouter, createWebHashHistory } from "vue-router";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: () => import("./pages/DashboardPage.vue"),
    },
    {
      path: "/login",
      name: "login",
      component: () => import("./pages/LoginPage.vue"),
    },
    {
      path: "/ocr",
      name: "ocr",
      component: () => import("./pages/OcrPage.vue"),
    },
    {
      path: "/history",
      name: "history",
      component: () => import("./pages/HistoryPage.vue"),
    },
    {
      path: "/ai-ad-copy",
      name: "ai-ad-copy",
      component: () => import("./pages/AdCopyPage.vue"),
    },
  ],
});

export default router;

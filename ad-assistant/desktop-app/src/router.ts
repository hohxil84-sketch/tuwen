/**
 * Vue Router — Sprint-01 skeleton.
 *
 * Pages allowed in Sprint-01:
 * - LoginPage
 * - OcrPage
 * - HistoryPage
 */
import { createRouter, createWebHashHistory } from "vue-router";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/login" },
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
  ],
});

export default router;

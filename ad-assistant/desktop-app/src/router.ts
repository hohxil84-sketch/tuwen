/**
 * Vue Router — Sprint-01 skeleton + Sprint-02 Task-05.
 *
 * Pages:
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

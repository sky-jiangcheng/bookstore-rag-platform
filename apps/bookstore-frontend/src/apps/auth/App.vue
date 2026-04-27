<template>
  <div class="app-shell auth-shell">
    <header class="auth-hero glass-panel">
      <p class="eyebrow">Identity</p>
      <h1 class="hero-title">认证中心</h1>
      <p class="hero-copy">
        独立登录、注册、会话管理入口，专门服务 RBAC 与用户身份链路。
      </p>
    </header>
    <main class="auth-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.auth-shell {
  padding: 32px;
  gap: 24px;
}

.auth-hero {
  padding: 28px 32px;
  max-width: 920px;
}

.auth-main {
  max-width: 920px;
}

.eyebrow {
  margin: 0 0 12px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #0ea5e9;
  font-size: 12px;
}
</style>

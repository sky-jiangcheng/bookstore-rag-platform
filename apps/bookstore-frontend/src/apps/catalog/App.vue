<template>
  <div class="app-shell catalog-shell">
    <header class="catalog-top glass-panel">
      <div>
        <p class="eyebrow eyebrow-amber">Catalog Console</p>
        <h1 class="hero-title">目录与运营控制台</h1>
        <p class="hero-copy">
          只保留图书、导入、补货、查重和屏蔽管理，专注库存与内容治理。
        </p>
      </div>
      <nav class="catalog-nav">
        <router-link to="/books">图书管理</router-link>
        <router-link to="/import">数据导入</router-link>
        <router-link to="/duplicates">智能查重</router-link>
        <router-link to="/filters">屏蔽配置</router-link>
        <router-link to="/purchase">采购管理</router-link>
        <router-link to="/replenishment">补货推荐</router-link>
      </nav>
    </header>
    <main class="catalog-stage glass-panel">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.catalog-shell {
  gap: 24px;
  padding: 24px;
}

.catalog-top {
  padding: 28px 32px;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
}

.catalog-nav {
  display: grid;
  grid-template-columns: repeat(2, minmax(140px, 1fr));
  gap: 12px;
  min-width: 320px;
}

.catalog-nav a {
  text-decoration: none;
  color: #111827;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(249, 115, 22, 0.1);
}

.catalog-nav a.router-link-active {
  background: linear-gradient(135deg, #f97316, #f59e0b);
  color: white;
}

.catalog-stage {
  padding: 28px;
  min-height: calc(100vh - 160px);
}

.eyebrow-amber {
  color: #f97316;
}

@media (max-width: 1024px) {
  .catalog-top {
    flex-direction: column;
  }

  .catalog-nav {
    width: 100%;
    min-width: unset;
  }
}
</style>

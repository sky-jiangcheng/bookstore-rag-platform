<template>
  <div class="app-shell rag-shell">
    <aside class="rag-rail glass-panel">
      <p class="eyebrow eyebrow-cyan">RAG Studio</p>
      <h1 class="hero-title">书单智能工作台</h1>
      <p class="hero-copy">
        只保留需求解析、Agent 推理、书单生成和分享，这里是 RAG 的独立前台。
      </p>
      <nav class="rag-nav">
        <router-link to="/booklist-recommendation">智能书单生成</router-link>
        <router-link to="/agent-booklist">Agent 书单</router-link>
        <router-link to="/demand-analysis">需求分析</router-link>
      </nav>
    </aside>
    <main class="rag-stage glass-panel">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.rag-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 24px;
  padding: 24px;
}

.rag-rail, .rag-stage {
  padding: 28px;
}

.rag-rail {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-self: start;
  position: sticky;
  top: 24px;
}

.rag-stage {
  min-height: calc(100vh - 48px);
}

.rag-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rag-nav a {
  text-decoration: none;
  color: #0f172a;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(14, 165, 233, 0.08);
}

.rag-nav a.router-link-active {
  background: linear-gradient(135deg, #0ea5e9, #22c55e);
  color: white;
}

.eyebrow-cyan {
  color: #06b6d4;
}

@media (max-width: 1024px) {
  .rag-shell {
    grid-template-columns: 1fr;
  }

  .rag-rail {
    position: static;
  }
}
</style>

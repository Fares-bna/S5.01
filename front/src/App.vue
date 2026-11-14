<script setup>
const etapes = ['01 Saisie', '02 Diagnostic', '03 Performances']
</script>

<template>
  <header class="app-header">
    <p class="brand-logo">
      DiagDuo<span>.</span>
    </p>
    <nav class="stepper-nav">
      <span
        v-for="(etape, index) in etapes"
        :key="etape"
        :class="{ active: index === 0 }"
      >
        {{ etape }}
      </span>
    </nav>
  </header>

  <main class="page-container">
    <section class="card-atelier">
      <h1 class="page-title">
        Squelette Front initialisé
      </h1>
      <p class="page-subtitle">
        Architecture MVC prête. Le lint et le build fonctionnent.
      </p>
    </section>
  </main>
</template>
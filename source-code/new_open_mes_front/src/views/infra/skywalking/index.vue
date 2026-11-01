<template>
  <ContentWrap>
    <IFrame v-if="src" :src="src" />
    <p v-else>请配置监控服务地址。</p>
  </ContentWrap>
</template>
<script setup lang="ts" name="Skywalking">
const src = ref(import.meta.env.VITE_SKYWALKING_URL || '')
</script>

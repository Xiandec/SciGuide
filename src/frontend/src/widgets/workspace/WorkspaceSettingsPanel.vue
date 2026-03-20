<script setup>
import WorkspaceDocumentsPanel from '@/widgets/workspace/WorkspaceDocumentsPanel.vue'
import WorkspaceOverviewPanel from '@/widgets/workspace/WorkspaceOverviewPanel.vue'
import WorkspacePromptPanel from '@/widgets/workspace/WorkspacePromptPanel.vue'

defineProps({
  workspace: {
    type: Object,
    required: true,
  },
  workspaceId: {
    type: String,
    required: true,
  },
  canManage: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['workspace-updated', 'workspace-deleted'])
</script>

<template>
  <section class="stack-lg">
    <WorkspaceOverviewPanel
      :workspace="workspace"
      :can-manage="canManage"
      @workspace-updated="$emit('workspace-updated', $event)"
      @workspace-deleted="$emit('workspace-deleted')"
    />
    <WorkspacePromptPanel :workspace-id="workspaceId" :can-manage="canManage" />
    <WorkspaceDocumentsPanel :workspace-id="workspaceId" :can-manage="canManage" />
  </section>
</template>

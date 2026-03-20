import { request } from '@/shared/api/http'

export function registerUser(payload) {
  return request('/auth/register', {
    method: 'POST',
    auth: false,
    data: payload,
  })
}

export function loginUser(credentials) {
  return request('/auth/login', {
    method: 'POST',
    auth: false,
    data: credentials,
  })
}

export function refreshTokens(payload) {
  return request('/auth/refresh', {
    method: 'POST',
    auth: false,
    data: payload,
  })
}

export function logoutUser(payload) {
  return request('/auth/logout', {
    method: 'POST',
    data: payload,
  })
}

export function fetchCurrentUser() {
  return request('/auth/me')
}

export function listWorkspaces(params) {
  return request('/workspaces', {
    params,
  })
}

export function createWorkspace(payload) {
  return request('/workspaces', {
    method: 'POST',
    data: payload,
  })
}

export function getWorkspace(workspaceId) {
  return request(`/workspaces/${workspaceId}`)
}

export function updateWorkspace(workspaceId, payload) {
  return request(`/workspaces/${workspaceId}`, {
    method: 'PATCH',
    data: payload,
  })
}

export function deleteWorkspace(workspaceId) {
  return request(`/workspaces/${workspaceId}`, {
    method: 'DELETE',
  })
}

export function listWorkspaceMembers(workspaceId) {
  return request(`/workspaces/${workspaceId}/members`)
}

export function addWorkspaceMember(workspaceId, payload) {
  return request(`/workspaces/${workspaceId}/members`, {
    method: 'POST',
    data: payload,
  })
}

export function updateWorkspaceMember(workspaceId, userId, payload) {
  return request(`/workspaces/${workspaceId}/members/${userId}`, {
    method: 'PATCH',
    data: payload,
  })
}

export function removeWorkspaceMember(workspaceId, userId) {
  return request(`/workspaces/${workspaceId}/members/${userId}`, {
    method: 'DELETE',
  })
}

export function getWorkspacePrompt(workspaceId) {
  return request(`/workspaces/${workspaceId}/prompt`)
}

export function updateWorkspacePrompt(workspaceId, payload) {
  return request(`/workspaces/${workspaceId}/prompt`, {
    method: 'PUT',
    data: payload,
  })
}

export function listWorkspaceDocuments(workspaceId, params) {
  return request(`/workspaces/${workspaceId}/documents`, {
    params,
  })
}

export function uploadWorkspaceDocument(workspaceId, { file, title }) {
  const formData = new FormData()

  formData.append('file', file)

  if (title) {
    formData.append('title', title)
  }

  return request(`/workspaces/${workspaceId}/documents`, {
    method: 'POST',
    data: formData,
  })
}

export function deleteWorkspaceDocument(workspaceId, documentId) {
  return request(`/workspaces/${workspaceId}/documents/${documentId}`, {
    method: 'DELETE',
  })
}

export function getDocumentProcessingStatus(workspaceId, documentId) {
  return request(`/workspaces/${workspaceId}/documents/${documentId}/processing`)
}

export function listWorkspaceChats(workspaceId, params) {
  return request(`/workspaces/${workspaceId}/chats`, {
    params,
  })
}

export function createWorkspaceChat(workspaceId, payload) {
  return request(`/workspaces/${workspaceId}/chats`, {
    method: 'POST',
    data: payload,
  })
}

export function updateWorkspaceChat(workspaceId, chatId, payload) {
  return request(`/workspaces/${workspaceId}/chats/${chatId}`, {
    method: 'PATCH',
    data: payload,
  })
}

export function deleteWorkspaceChat(workspaceId, chatId) {
  return request(`/workspaces/${workspaceId}/chats/${chatId}`, {
    method: 'DELETE',
  })
}

export function listChatMessages(workspaceId, chatId, params) {
  return request(`/workspaces/${workspaceId}/chats/${chatId}/messages`, {
    params,
  })
}

export function createChatMessage(workspaceId, chatId, payload) {
  return request(`/workspaces/${workspaceId}/chats/${chatId}/messages`, {
    method: 'POST',
    data: payload,
  })
}

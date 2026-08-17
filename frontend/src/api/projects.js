import service from './index'

export const getUserProject = (projectId) => {
  return service.get(`/api/projects/${projectId}`)
}

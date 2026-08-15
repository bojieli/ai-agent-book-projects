import { request } from '../utils/http';

/**
 * 工作空间树节点数据结构
 */
export interface WorkspaceTreeResponse {
  id: string;          // 节点ID
  name: string;        // 节点名称
  type: string;        // 节点类型 (dir/file)
  parentId: string | null; // 父节点ID
  depth: number;       // 节点深度
  expanded: boolean;   // 是否展开
  children: WorkspaceTreeResponse[]; // 子节点列表
}

/**
 * Get Artifact的请求参数
 */
export interface ArtifactQueryRequest {
  artifact_types: string[];    // Artifact类型
  artifact_ids: string[];    // Artifact ID
}

/**
 * 创建Artifact的请求参数
 */
export interface ArtifactCreateRequest {
  name: string;    // Artifact名称
  type: string;    // Artifact类型
  content: any;    // Artifact内容
}

/**
 * 创建Artifact的响应数据
 */
export interface ArtifactCreateResponse {
  id: string;                     // 创建的Artifact ID
  status: 'success' | 'failed';   // 操作状态
  message?: string;               // 可选的状态信息
}

/**
 * 获取工作空间树
 */
export const getWorkspaceTree = (sessionId: string) =>
  request(`api/workspaces/${sessionId}/tree`);


/**
 * 获取工作空间Artifacts
 */
export const getWorkspaceArtifacts = (sessionId: string, body: ArtifactQueryRequest) =>
  request(`api/workspaces/${sessionId}/artifacts`, {
    method: 'POST',
    body
  });


/**
 * 创建工作空间Artifact
 */
export const createArtifact = (workspaceId: string, body: ArtifactCreateRequest) =>
  request(`api/workspaces/${workspaceId}/artifacts`, {
    method: 'POST',
    body
  });

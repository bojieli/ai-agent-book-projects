import { getWorkspaceArtifacts } from '@/api/workspace';
import { Image, Typography } from 'antd';
import React, { useEffect, useRef, useState } from 'react';
import type { ToolCardData } from '../../BubbleItem/utils';
import './index.less';

interface ArtifactItem {
  snippet: string;
  link: string;
  key: string;
  title: string;
  content: string;
}

interface WorkspaceProps {
  sessionId: string;
  toolCardData: ToolCardData;
}

const Workspace: React.FC<WorkspaceProps> = ({ sessionId, toolCardData }) => {
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [imgUrl, setImgUrl] = useState<string | undefined>();
  const isLinkListCard = toolCardData?.card_type === 'tool_call_card_link_list';

  // 用于缓存上次的请求参数，避免重复调用
  const lastRequestRef = useRef<{
    sessionId: string;
    artifactType: string;
    artifactId: string;
  } | null>(null);

  useEffect(() => {
    if (!toolCardData) return; // 如果没有 toolCardData，直接退出

    const fetchWorkspaceArtifacts = async () => {
      try {
        const artifactType = toolCardData.artifacts?.[0]?.artifact_type;
        const artifactId = toolCardData.artifacts?.[0]?.artifact_id;

        if (!artifactType || !artifactId) {
          console.warn('Invalid artifact data');
          return;
        }

        // 检查是否与上次请求参数相同
        const currentRequest = {
          sessionId,
          artifactType,
          artifactId
        };

        if (lastRequestRef.current &&
          lastRequestRef.current.sessionId === currentRequest.sessionId &&
          lastRequestRef.current.artifactType === currentRequest.artifactType &&
          lastRequestRef.current.artifactId === currentRequest.artifactId) {
          // 参数相同，跳过重复请求
          return;
        }

        // 更新缓存的请求参数
        lastRequestRef.current = currentRequest;

        const data = await getWorkspaceArtifacts(sessionId, {
          artifact_types: [artifactType],
          artifact_ids: [artifactId]
        });

        const content = data?.data?.[0]?.content;

        if (isLinkListCard) {
          setArtifacts(Array.isArray(content) ? content : []);
        } else {
          setImgUrl(content);
        }
      } catch (error) {
        console.error('Failed to fetch workspace artifacts:', error);
      }
    };

    fetchWorkspaceArtifacts();
  }, [sessionId, toolCardData, isLinkListCard]);

  const renderArtifactsList = () => (
    <div className="listbox">
      {artifacts.map((item, index) => (
        <div className="list" key={index}>
          <Typography.Link href={item?.link} target="_blank">
            <Typography.Paragraph className="name" ellipsis={{ rows: 1 }}>
              {item?.title}
            </Typography.Paragraph>
            <Typography.Paragraph className="desc" ellipsis={{ rows: 3 }}>
              {item?.snippet}
            </Typography.Paragraph>
            <Typography.Paragraph className="link" ellipsis={{ rows: 1 }}>
              {item?.link}
            </Typography.Paragraph>
          </Typography.Link>
        </div>
      ))}
    </div>
  );

  const renderImage = () => <Image preview={false} src={imgUrl} alt="Workspace Artifact" />;

  return (
    <div className="workspacebox">
      <div className="border listwrap">
        {isLinkListCard ? renderArtifactsList() : renderImage()}
      </div>
    </div>
  );
};

export default Workspace;

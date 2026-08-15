import { CheckOutlined, MenuUnfoldOutlined, SearchOutlined } from '@ant-design/icons';
import { Button, Card, Flex, Tag, Typography } from 'antd';
import React, { useCallback } from 'react';
import type { ToolCardData } from '../utils';
import './index.less';

interface Props {
  sessionId: string;
  data: ToolCardData;
  onOpenWorkspace?: (data: ToolCardData) => void;
}

interface ItemInterface {
  title: string;
  snippet: string;
  link?: string;
}

const cardLinkList: React.FC<Props> = ({ sessionId, data, onOpenWorkspace }) => {
  const items = data?.card_data?.search_items;

  const cardItems = Array.isArray(items) ? items.filter((item) => item?.title && item?.link) : [];
  // 打开workspace
  const handleOpenWorkspace = useCallback(() => {
    if (onOpenWorkspace) {
      onOpenWorkspace(data);
    }
  }, [onOpenWorkspace, sessionId, data]);

  return (
    <div className="cardwrap bg">
      <Button type="link" className="btn-workspace" icon={<MenuUnfoldOutlined />} onClick={handleOpenWorkspace}>
        View Workspace
      </Button>
      <Flex justify="space-between" align="center" className="card-length">
        <Tag icon={<SearchOutlined />}>{`search keywords: ${data?.card_data?.query || ''}`}</Tag>
        <Flex align="center">
          <CheckOutlined className="check-icon" />
          {cardItems.length} results
        </Flex>
      </Flex>
      <div className="border-box">
        <Flex className="cardbox">
          {cardItems?.map((item: ItemInterface, index: number) => (
            <Card title={item?.title} key={index} className="card-item" onClick={() => item?.link && window.open(item?.link, '_blank', 'noopener,noreferrer')}>
              <Typography.Paragraph className="desc" ellipsis={{ rows: 3, tooltip: typeof item?.snippet === 'string' ? item?.snippet : '' }}>
                {item?.snippet}
              </Typography.Paragraph>
              <Typography.Text ellipsis={{ tooltip: typeof item?.link === 'string' ? item?.link : '' }}>{item?.link}</Typography.Text>
            </Card>
          ))}
        </Flex>
      </div>
    </div>
  );
};

export default cardLinkList;

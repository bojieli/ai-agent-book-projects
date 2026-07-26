import {
  AlertFilled,
  BoxPlotOutlined,
  CloudUploadOutlined,
  CopyOutlined,
  DeleteOutlined,
  MessageOutlined,
  PaperClipOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  VerticalLeftOutlined,
  VerticalRightOutlined
} from '@ant-design/icons';
import {
  Attachments,
  Bubble,
  Conversations,
  Sender,
  useXAgent,
  useXChat
} from '@ant-design/x';
import { Avatar, Button, Flex, type GetProp, message, Spin, Tabs } from 'antd';
import { createStyles } from 'antd-style';
import React, { useEffect, useRef, useState } from 'react';
import logo from '../assets/aworld_logo.png';
import { useAgentId } from '../hooks/useAgentId';
import { useSessionId } from '../hooks/useSessionId';
import Prompts from '../pages/components/Prompts';
import Welcome from '../pages/components/Welcome';
import BubbleItem from './components/BubbleItem';
// import Trace from './components/Drawer/TraceThoughtChain';
import TraceXY from './components/Drawer/TraceXY';
import Workspace from './components/Drawer/Workspace';
import './index.less';

type BubbleDataType = {
  role: string;
  content: string;
  trace_id?: string;
};

// 添加会话数据类型定义
type SessionMessage = {
  role: string;
  content: string;
  trace_id?: string;
};

type SessionData = {
  user_id: string;
  session_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  messages: SessionMessage[];
};

// 会话列表项类型
type ConversationItem = {
  key: string;
  label: string;
  group: string;
};

const DEFAULT_CONVERSATIONS_ITEMS: ConversationItem[] = [];

const SENDER_PROMPTS: GetProp<typeof Prompts, 'items'> = [];

const useStyle = createStyles(({ token, css }) => {
  return {
    layout: css`
      width: 100%;
      min-width: 1000px;
      height: 100vh;
      display: flex;
      background: ${token.colorBgContainer};
      font-family: AlibabaPuHuiTi, ${token.fontFamily}, sans-serif;
    `,
    // sider 样式
    sider: css`
      background: ${token.colorBgLayout}80;
      width: 280px;
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: 0 12px;
      box-sizing: border-box;
      transition: width 0.3s ease, padding 0.3s ease;
      position: relative;
      border-right: 1px solid ${token.colorBorderSecondary};
      
      &.collapsed {
        width: 60px;
        padding: 0 8px;
      }
      
      &.expanded {
      }
      
      .sider-content {
        display: flex;
        flex-direction: column;
        height: 100%;
        flex: 1;
        opacity: 1;
        visibility: visible;
        transition: opacity 0.3s ease, visibility 0.3s ease;
      }
    `,
    collapseButton: css`
      position: absolute;
      top: 50%;
      right: -10px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: ${token.colorBgContainer};
      border: 1px solid ${token.colorBorderSecondary};
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 1000;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
      transition: all 0.2s ease;
      transform: translateY(-50%);
      
      &:hover {
        background: ${token.colorBgTextHover};
        transform: translateY(-50%) scale(1.15);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        border-color: ${token.colorPrimary};
      }
      
      .anticon {
        font-size: 10px;
        color: ${token.colorTextTertiary};
        transition: color 0.2s ease;
      }
      
      &:hover .anticon {
        color: ${token.colorPrimary};
      }
    `,
    logo: css`
      display: flex;
      align-items: center;
      justify-content: start;
      box-sizing: border-box;
      gap: 8px;
      margin: 24px 0;
      transition: justify-content 0.3s ease;
      text-decoration: none;

      span {
        font-weight: bold;
        color: ${token.colorText};
        font-size: 16px;
        transition: opacity 0.3s ease;
      }
      
      &.centered {
        justify-content: center;
        
        span {
          opacity: 0;
          width: 0;
          overflow: hidden;
        }
      }
    `,
    addBtn: css`
      background: #1677ff0f;
      border: 1px solid #1677ff34;
      height: 40px;
    `,
    conversations: css`
      flex: 1;
      overflow-y: auto;
      margin-top: 12px;
      padding: 0;

      .ant-conversations-list {
        padding-inline-start: 0;
      }
    `,
    siderFooter: css`
      border-top: 1px solid ${token.colorBorderSecondary};
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    `,
    // chat list 样式
    chat: css`
      height: 100%;
      width: 100%;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      padding-block: ${token.paddingLG}px;
      gap: 16px;
      transition: margin-left 0.3s ease, margin-right 0.3s ease;
    `,
    chatPrompt: css`
      .ant-prompts-label {
        color: #000000e0 !important;
      }
      .ant-prompts-desc {
        color: #000000a6 !important;
        width: 100%;
      }
      .ant-prompts-icon {
        color: #000000a6 !important;
      }
    `,
    chatList: css`
      flex: 1;
      overflow: auto;
    `,
    loadingMessage: css`
      background-image: linear-gradient(90deg, #ff6b23 0%, #af3cb8 31%, #53b6ff 89%);
      background-size: 100% 2px;
      background-repeat: no-repeat;
      background-position: bottom;
    `,
    placeholder: css`
      width: 100%;
      max-width: 700px;
      margin: 0 auto;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
    `,
    // sender 样式
    sender: css`
      width: 100%;
      max-width: 700px;
      margin: 0 auto;
    `,
    speechButton: css`
      font-size: 18px;
      color: ${token.colorText} !important;
    `,
    senderPrompt: css`
      width: 100%;
      max-width: 700px;
      margin: 0 auto;
      color: ${token.colorText};
    `,
    sendButton: css`
      background-color: #000000 !important;
      border: none !important;
      transition: opacity 0.2s;
      
      &:hover {
        background-color: rgba(0, 0, 0, 0.7) !important;
      }
      
      &:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed;
        background-color: rgba(0, 0, 0, 0.1) !important;
      }
      
      &:disabled:hover,
      &:disabled:focus {
        opacity: 0.5 !important;
        background-color: rgba(0, 0, 0, 0.1) !important;
      }
    `,

  };
});

const App: React.FC = () => {
  const { styles } = useStyle();
  const abortController = useRef<AbortController | null>(null);
  const { sessionId, generateNewSessionId, updateURLSessionId, setSessionId } = useSessionId();
  const { agentId, setAgentIdAndUpdateURL } = useAgentId();

  // ==================== State ====================
  const [siderCollapsed, setSiderCollapsed] = useState(true);
  const [messageHistory, setMessageHistory] = useState<Record<string, any>>({});
  const [sessionData, setSessionData] = useState<Record<string, SessionData>>({});
  const [conversations, setConversations] = useState<ConversationItem[]>(DEFAULT_CONVERSATIONS_ITEMS);
  const [curConversation, setCurConversation] = useState<string>('');
  const [attachmentsOpen, setAttachmentsOpen] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<GetProp<typeof Attachments, 'items'>>([]);
  const [inputValue, setInputValue] = useState('');
  const [models, setModels] = useState<Array<{ label: string; value: string }>>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [modelsLoading, setModelsLoading] = useState(false);

  // 右侧侧边栏
  type SiderContentType = 'TraceXY' | 'Workspace';
  const [rightSiderCollapsed, setRightSiderCollapsed] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('TraceXY');
  const [traceId, setTraceId] = useState<string>('');
  const [traceQuery, setTraceQuery] = useState<string>('');
  const [workspaceData, setWorkspaceData] = useState<any>(null);

  // ==================== 公共样式常量 ====================
  const collapsedButtonStyle = {
    width: '40px',
    height: '40px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid #1677ff34',
    borderRadius: '8px',
    transition: 'all 0.2s ease'
  };

  const buttonHoverHandlers = {
    onMouseEnter: (e: React.MouseEvent<HTMLElement>) => {
      e.currentTarget.style.backgroundColor = '#1677ff0f';
      e.currentTarget.style.borderColor = '#1677ff';
      e.currentTarget.style.transform = 'scale(1.05)';
    },
    onMouseLeave: (e: React.MouseEvent<HTMLElement>) => {
      e.currentTarget.style.backgroundColor = 'transparent';
      e.currentTarget.style.borderColor = '#1677ff34';
      e.currentTarget.style.transform = 'scale(1)';
    }
  };

  const tabContentStyle = { height: 'calc(100vh - 50px)', overflow: 'auto' };
  const emptyStateStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '200px',
    color: '#999'
  };

  // ==================== 公共函数 ====================
  const createNewConversation = () => {
    if (conversations.some(conv => conv.label === 'New Conversation')) {
      message.warning('New session already exists, please ask a question.');
      return;
    }

    if (agent.isRequesting()) {
      message.error('Message is Requesting, you can create a new conversation after request done or abort it right now...');
      return;
    }

    // 关闭右侧侧边栏
    setRightSiderCollapsed(true);

    // 生成新的session ID
    const newSessionId = generateNewSessionId();

    // 创建新的会话项
    const newConversation: ConversationItem = {
      key: newSessionId,
      label: 'New Conversation',
      group: '',
    };

    setConversations([newConversation, ...conversations]);
    setCurConversation(newSessionId);
    setMessages([]);
  };

  const openRightSider = (content: SiderContentType, data?: any) => {
    console.log('openRightSider', content, data);
    setRightSiderCollapsed(false);
    setSiderCollapsed(true);
    setActiveTab(content);

    if (content === 'TraceXY' && data) {
      setTraceId(data);
      const session = sessionData[sessionId];
      if (session?.messages) {
        const userItem = session.messages.find(msg => msg.trace_id === data && msg.role === 'user');
        if (userItem) {
          setTraceQuery(userItem.content);
        }
      }
    } else if (content === 'Workspace' && data) {
      setWorkspaceData(data);
    }
  };

  const handleSessionChange = async (val: string) => {
    try {
      // 先从服务端刷新session列表
      await fetchSessions();

      // 然后设置当前选中的session
      setCurConversation(val);
      setSessionId(val);
      updateURLSessionId(val);

      // 使用刷新后的sessionData来获取当前session的消息
      const session = sessionData[val];
      if (session?.messages.length > 0) {
        const chatMessages = session.messages.map((msg, index) => ({
          id: `${val}-${index}`,
          message: {
            role: msg.role,
            trace_id: msg.trace_id,
            content: msg.content
          },
          status: 'success' as const
        }));
        setMessages(chatMessages);
      } else {
        setMessages(messageHistory?.[val] || []);
      }
    } catch (error) {
      console.error('Error fetching session data:', error);
    }
  };

  const deleteSession = async (sessionKey: string) => {
    try {
      const response = await fetch('/api/session/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionKey }),
      });
      const data = await response.json();

      if (data.code === 0) {
        message.success('Session deleted');
        fetchSessions();
      } else {
        message.error('Failed to delete session');
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      message.error('Failed to delete session');
    }
  };

  // ==================== API Calls ====================
  const fetchModels = async () => {
    setModelsLoading(true);
    try {
      const response = await fetch('/api/agent/models');
      if (response.ok) {
        const data = await response.json();
        const modelOptions = Object.values(data).map((model: any) => ({
          label: model.name || model.id,
          value: model.id
        }));
        setModels(modelOptions);
      } else {
        message.error('Failed to fetch models');
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      message.error('Error fetching models');
    } finally {
      setModelsLoading(false);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch('/api/session/list');
      if (response.ok) {
        const sessions: SessionData[] = await response.json();

        const sessionDataMap: Record<string, SessionData> = {};
        sessions.forEach(session => {
          sessionDataMap[session.session_id] = session;
        });
        setSessionData(sessionDataMap);

        const conversationItems: ConversationItem[] = sessions.map(session => {
          let label = session.name || session.description;
          if (!label && session.messages.length > 0) {
            const firstUserMessage = session.messages.find(msg => msg.role === 'user');
            if (firstUserMessage) {
              label = firstUserMessage.content.length > 50
                ? firstUserMessage.content.substring(0, 50) + '...'
                : firstUserMessage.content;
            } else {
              label = 'New Conversation';
            }
          }
          if (!label) {
            label = 'New Conversation';
          }

          return {
            key: session.session_id,
            label,
            group: ''
          };
        });

        setConversations(conversationItems);
      } else {
        console.error('Failed to fetch sessions');
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  useEffect(() => {
    fetchModels();
    fetchSessions();
  }, []);

  useEffect(() => {
    if (agentId && models.length > 0) {
      const modelExists = models.find(model => model.value === agentId);
      setSelectedModel(modelExists ? agentId : '');
      if (!modelExists) {
        setAgentIdAndUpdateURL('');
      }
    }
  }, [agentId, models, setAgentIdAndUpdateURL]);

  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
    setAgentIdAndUpdateURL(modelId);
  };

  /**
   * 🔔 Please replace the BASE_URL, PATH, MODEL, API_KEY with your own values.
   */

  // ==================== Runtime ====================
  const [agent] = useXAgent<BubbleDataType>({
    baseURL: '/api/agent/chat/completions',
    model: selectedModel,
    dangerouslyApiKey: 'Bearer local-debug-token',
  });
  const loading = agent.isRequesting();

  const { onRequest, messages, setMessages } = useXChat({
    agent,
    requestFallback: (_, { error }) => {
      if (error.name === 'AbortError') {
        return {
          content: 'Request is aborted',
          role: 'assistant',
        };
      }
      return {
        content: 'Request failed, please try again!',
        role: 'assistant',
      };
    },
    transformMessage: (info) => {
      const { originMessage, chunk } = info || {};
      let currentContent = '';
      let currentThink = '';
      let currentTraceId = '';
      try {
        if (chunk?.data && !chunk?.data.includes('DONE')) {
          const message = JSON.parse(chunk?.data);
          const traceId = message?.choices?.[0]?.delta?.trace_id;
          if (traceId) {
            currentTraceId = traceId;
          }
          currentThink = message?.choices?.[0]?.delta?.reasoning_content || '';
          currentContent = message?.choices?.[0]?.delta?.content || '';
        }
      } catch (error) {
        console.error(error);
      }

      let content = '';

      if (!originMessage?.content && currentThink) {
        content = `<think>${currentThink}`;
      } else if (
        originMessage?.content?.includes('<think>') &&
        !originMessage?.content.includes('</think>') &&
        currentContent
      ) {
        content = `${originMessage?.content}</think>${currentContent}`;
      } else {
        content = `${originMessage?.content || ''}${currentThink}${currentContent}`;
      }
      if (!chunk && originMessage?.trace_id) {
        currentTraceId = originMessage?.trace_id
      }
      return {
        content: content,
        role: 'assistant',
        trace_id: currentTraceId
      };
    },
    resolveAbortController: (controller) => {
      if (abortController.current) {
        abortController.current.abort();
      }
      abortController.current = controller;
    },
  });

  // ==================== Event ====================
  const toggleSiderCollapse = () => {
    const newCollapsed = !siderCollapsed;
    setSiderCollapsed(newCollapsed);
    if (!newCollapsed) {
      setRightSiderCollapsed(true);
    }
  };

  const onSubmit = (val: string) => {
    if (!val?.trim()) return;

    if (loading) {
      message.error('Request is in progress, please wait for the request to complete.');
      return;
    }

    onRequest({
      stream: true,
      session_id: sessionId,
      message: { role: 'user', content: val },
    });
    setTraceQuery(val);
  };

  const copyMessageContent = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      message.success('Message copied to clipboard');
    } catch (error) {
      console.error('Failed to copy message:', error);
      message.error('Failed to copy message');
    }
  };

  // ==================== 组件渲染函数 ====================
  const renderCollapsedSider = () => (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', marginTop: '20px', flex: 1 }}>
        <Button
          type="text"
          icon={<PlusOutlined />}
          size="large"
          style={collapsedButtonStyle}
          title="New Conversation"
          {...buttonHoverHandlers}
          onClick={createNewConversation}
        />

        {conversations.length > 0 && (
          <div style={{
            position: 'relative',
            ...collapsedButtonStyle,
            border: '1px solid #d9d9d9',
            backgroundColor: curConversation ? '#1677ff0f' : 'transparent',
            cursor: 'pointer'
          }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#1677ff0f';
              e.currentTarget.style.borderColor = '#1677ff';
              e.currentTarget.style.transform = 'scale(1.05)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = curConversation ? '#1677ff0f' : 'transparent';
              e.currentTarget.style.borderColor = '#d9d9d9';
              e.currentTarget.style.transform = 'scale(1)';
            }}
            onClick={() => {
              setSiderCollapsed(false);
              setRightSiderCollapsed(true);
            }}
            title={`${conversations.length} Conversations - Click to expand`}
          >
            <Button
              type="text"
              icon={<MessageOutlined />}
              size="large"
              style={{ border: 'none', background: 'transparent', pointerEvents: 'none' }}
            />
            <span style={{
              position: 'absolute',
              top: '-6px',
              right: '-6px',
              backgroundColor: '#ff4d4f',
              color: 'white',
              borderRadius: '50%',
              width: '18px',
              height: '18px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold'
            }}>
              {conversations.length > 99 ? '99+' : conversations.length}
            </span>
          </div>
        )}
      </div>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
        borderTop: '1px solid #f0f0f0',
        paddingTop: '12px',
        marginTop: 'auto'
      }}>
        <Avatar size={32} />
        <Button
          type="text"
          icon={<QuestionCircleOutlined />}
          size="large"
          style={collapsedButtonStyle}
          title="Help"
        />
      </div>
    </>
  );

  const renderExpandedSider = () => (
    <>
      <Button
        onClick={createNewConversation}
        type="link"
        className={styles.addBtn}
        icon={<PlusOutlined />}
      >
        New Conversation
      </Button>

      <Conversations
        items={conversations}
        className={styles.conversations}
        activeKey={curConversation}
        onActiveChange={handleSessionChange}
        groupable={false}
        styles={{ item: { padding: '0 8px' } }}
        menu={(conversation) => ({
          items: [
            {
              label: 'Delete',
              key: 'delete',
              icon: <DeleteOutlined />,
              danger: true,
              onClick: () => deleteSession(conversation.key),
            },
          ],
        })}
      />

      <div className={styles.siderFooter}>
        <Avatar size={24} />
        <Button type="text" icon={<QuestionCircleOutlined />} />
      </div>
    </>
  );

  // ==================== Nodes ====================
  const chatSider = (
    <div className={`${styles.sider} ${siderCollapsed ? 'collapsed' : 'expanded'}`}>
      <div className={styles.collapseButton} onClick={toggleSiderCollapse}>
        {siderCollapsed ? <VerticalLeftOutlined /> : <VerticalRightOutlined />}
      </div>

      <div className="sider-content">
        <a href="https://github.com/inclusionAI/AWorld" className={`${styles.logo} ${siderCollapsed ? 'centered' : ''}`} target="_blank">
          <img src={logo} alt="AWorld Logo" width="32" height="32" />
          {!siderCollapsed && <span>AWorld</span>}
        </a>

        {siderCollapsed ? renderCollapsedSider() : renderExpandedSider()}
      </div>
    </div>
  );
  const renderMessageActions = (messageItem: any) => {
    console.log("renderMessageActions", messageItem);
    const actions = [
      {
        icon: <CopyOutlined />,
        onClick: () => copyMessageContent(messageItem.content || ''),
        key: 'copy'
      },
      {
        icon: <BoxPlotOutlined />,
        onClick: () => openRightSider('TraceXY', messageItem.props?.trace_id),
        key: 'trace'
      },
      {
        icon: <AlertFilled />,
        onClick: () => window.open('/trace_ui.html', '_blank'),
        key: 'alert'
      }
    ];

    return (
      <div style={{ display: 'flex' }}>
        {actions.map(action => (
          <Button
            key={action.key}
            type="text"
            size="small"
            icon={action.icon}
            onClick={action.onClick}
          />
        ))}
      </div>
    );
  };

  const chatList = (
    <div className={styles.chatList}>
      {messages?.length ? (
        <Bubble.List
          items={messages.map((i, _) => ({
            ...i.message,
            content: (
              <BubbleItem
                sessionId={sessionId}
                data={i.message.content || ''}
                trace_id={i.message?.trace_id || ''}
                onOpenWorkspace={(data) => openRightSider('Workspace', data)}
                isLoading={i.status === 'loading'}
              />
            ),
            classNames: {
              content: i.status === 'loading' ? styles.loadingMessage : '',
            },
            typing: i.status === 'loading' ? { step: 5, interval: 20, suffix: <>💗</> } : false,
            styles: {
              content: {
                backgroundColor: '#f5f5f5',
                maxWidth: '98%'
              }
            }
          }))}
          style={{
            height: '100%',
            paddingInline: '10px',
            margin: '0 auto',
            maxWidth: `calc(100vw - ${siderCollapsed ? '60px' : '280px'} - ${rightSiderCollapsed ? '0px' : '500px'} - 40px)`
          }}
          roles={{
            assistant: {
              placement: 'start',
              footer: renderMessageActions,
              loadingRender: () => <Spin size="small" />,
            },
            user: { placement: 'end' },
          }}
        />
      ) : (
        <div className={styles.placeholder}>
          <Welcome
            onSubmit={(v: string) => {
              if (v?.trim()) {
                onSubmit(v);
                setInputValue('');
              }
            }}
            models={models}
            selectedModel={selectedModel}
            onModelChange={handleModelChange}
            modelsLoading={modelsLoading}
          />
        </div>
      )}
    </div>
  );
  const handleSenderSubmit = () => {
    if (inputValue.trim()) {
      onSubmit(inputValue);
      setInputValue('');
    }
  };

  const renderSenderActions = (_: any, info: any) => {
    const { SendButton, LoadingButton, SpeechButton } = info.components;
    return (
      <Flex gap={4}>
        <SpeechButton className={styles.speechButton} />
        {loading ? (
          <LoadingButton type="default" />
        ) : (
          <SendButton
            type="primary"
            disabled={!inputValue.trim()}
            className={styles.sendButton}
          />
        )}
      </Flex>
    );
  };

  const senderHeader = (
    <Sender.Header
      title="Upload File"
      open={attachmentsOpen}
      onOpenChange={setAttachmentsOpen}
      styles={{ content: { padding: 0 } }}
    >
      <Attachments
        beforeUpload={() => false}
        items={attachedFiles}
        onChange={(info) => setAttachedFiles(info.fileList)}
        placeholder={(type) =>
          type === 'drop'
            ? { title: 'Drop file here' }
            : {
              icon: <CloudUploadOutlined />,
              title: 'Upload files',
              description: 'Click or drag files to this area to upload',
            }
        }
      />
    </Sender.Header>
  );

  const chatSender = (
    <>
      <Prompts
        items={SENDER_PROMPTS}
        onItemClick={(info) => {
          const description = info.data.description as string;
          if (description?.trim()) {
            onSubmit(description);
          }
        }}
        className={styles.senderPrompt}
      />
      <Sender
        value={inputValue}
        header={senderHeader}
        onSubmit={handleSenderSubmit}
        onChange={setInputValue}
        onCancel={() => abortController.current?.abort()}
        prefix={
          <Button
            type="text"
            icon={<PaperClipOutlined style={{ fontSize: 18 }} />}
            onClick={() => setAttachmentsOpen(!attachmentsOpen)}
          />
        }
        loading={loading}
        className={styles.sender}
        allowSpeech
        actions={renderSenderActions}
        placeholder="Ask or input / use skills"
      />
    </>
  );

  useEffect(() => {
    if (messages?.length && curConversation) {
      setMessageHistory((prev) => ({
        ...prev,
        [curConversation]: messages,
      }));
    }
  }, [messages, curConversation]);

  // ==================== Render =================
  return (
    <div className={styles.layout}>
      {chatSider}
      <div className={styles.chat} style={{
        transition: 'margin-right 0.3s ease'
      }}>
        {chatList}
        {messages?.length > 0 && chatSender}
      </div>
      {!rightSiderCollapsed && (
        <div className={`${styles.sider} ${rightSiderCollapsed ? 'collapsed' : 'expanded'}`} style={{
          right: 0,
          width: '500px',
          flexShrink: 0,
          borderLeft: '1px solid #f0f0f0',
          borderRight: 'none'
        }}>
          <div className={styles.collapseButton} style={{ left: '-10px', right: 'auto' }} onClick={() => setRightSiderCollapsed(true)}>
            <VerticalLeftOutlined />
          </div>

          <div className="sider-content">
            {activeTab === 'Workspace' && (
              <Tabs
                size="small"
                style={{ height: '100%' }}
                items={[
                  {
                    key: "Workspace",
                    label: "Workspace",
                    children: (
                      <div style={tabContentStyle}>
                        {workspaceData ? (
                          <Workspace
                            key={`workspace-${rightSiderCollapsed}`}
                            sessionId={sessionId}
                            toolCardData={workspaceData}
                          />
                        ) : (
                          <div style={emptyStateStyle}>
                            No workspace data available
                          </div>
                        )}
                      </div>
                    )
                  }
                ]}
              />
            )}
            {activeTab === 'TraceXY' && (
              <Tabs
                size="small"
                style={{ height: '100%' }}
                items={[
                  {
                    key: "TraceXY",
                    label: "Trace",
                    children: (
                      <div style={tabContentStyle}>
                        <TraceXY
                          key={`${traceId}-${rightSiderCollapsed}`}
                          traceId={traceId}
                          traceQuery={traceQuery}
                          drawerVisible={!rightSiderCollapsed}
                        />
                      </div>
                    )
                  }
                ]}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default App;

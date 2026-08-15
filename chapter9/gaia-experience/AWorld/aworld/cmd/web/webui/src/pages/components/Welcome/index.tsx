import { ArrowUpOutlined, RightOutlined } from '@ant-design/icons';
import { Button, Col, Flex, Input, Row, Select, Typography } from 'antd';
import React, { useState } from 'react';
import logo from '../../../assets/aworld_logo.png';
import './index.less';

const { Title } = Typography;

interface WelcomeProps {
  onSubmit: (value: string) => void;
  models: Array<{ label: string; value: string }>;
  selectedModel: string;
  onModelChange: (value: string) => void;
  modelsLoading: boolean;
}

const Welcome: React.FC<WelcomeProps> = ({
  onSubmit,
  models,
  selectedModel,
  onModelChange,
  modelsLoading,
}) => {
  const [inputValue, setInputValue] = useState('');
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputValue.trim()) onSubmit(inputValue);
    }
  };

  return (
    <div className="welcome-container">
      <div className="content">
        <Row justify="center">
          <Col>
            <div className="logo-title-container">
              <img src={logo} alt="AWorld Logo" width="46" height="46" />
              <Title level={1} style={{ margin: 0 }}>
                <a
                  href="https://github.com/inclusionAI/AWorld"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="aworld-link"
                >
                  Hello{' '}AWorld
                </a>
              </Title>
            </div>
          </Col>
        </Row>
        <div className="input-area">
          <Input.TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask or input / use skills"
            autoSize={{ minRows: 3, maxRows: 5 }}
            className="text-input"
          />
          <Button
            type="primary"
            shape="circle"
            onClick={() => {
              if (inputValue.trim()) onSubmit(inputValue);
            }}
            icon={<ArrowUpOutlined />}
            className="submit-button"
            disabled={inputValue.trim() === ''}
          />
        </div>
        <div className="controls-area">
          <Select
            value={selectedModel}
            onChange={onModelChange}
            options={models}
            loading={modelsLoading}
            placeholder="Select a model"
            className="model-select"
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            optionRender={(option) => (
              <div className="select-item">
                <Flex justify="space-between">
                  <div>
                    <strong>{option.label}</strong>
                    <small>{option.value}</small>
                  </div>
                  <RightOutlined className="icon-right" />
                </Flex>
              </div>
            )}
          />
        </div>
      </div>
    </div>
  );
};

export default Welcome;

import {
    Prompts as AntDesignPrompts,
  } from '@ant-design/x';

import './index.less';

interface IPromptsProps {
    items: any[];
    onItemClick: (item: any) => void;
    className?: string;
}

const Prompts = (props: IPromptsProps) => {
    const { items, onItemClick, className } = props;
    return (
        <AntDesignPrompts
        items={items}
        styles={{
          item: {
            flex: 1,
            backgroundImage: 'linear-gradient(123deg, #e5f4ff 0%, #efe7ff 100%)',
            borderRadius: 12,
            border: 'none',
          },
          subItem: { background: '#ffffffa6' },
        }}
        onItemClick={(info) => {
            onItemClick(info.data.description as string )
        }}
        className={className || "chatPrompt"}
        
        />
    )
}

export default Prompts;
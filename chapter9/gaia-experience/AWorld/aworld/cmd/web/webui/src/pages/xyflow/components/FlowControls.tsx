import { Controls, ControlButton } from '@xyflow/react';
import { PlusOutlined, SaveOutlined, FolderOutlined, ReloadOutlined, GlobalOutlined, UndoOutlined, RedoOutlined } from '@ant-design/icons';
import type { FC } from 'react';
interface FlowControlsProps {
  isStraightLine: boolean;
  showMinimap: boolean;
  onToggleLine: () => void;
  onSave: () => void;
  onLoad: () => void;
  onAutoLayout: () => void;
  onToggleMinimap: () => void;
  onAddNode: () => void;
  onUndo: () => void;
  onRedo: () => void;
}

export const FlowControls: FC<FlowControlsProps> = ({ 
  isStraightLine, 
  showMinimap, 
  onToggleLine, 
  onSave, 
  onLoad, 
  onAutoLayout, 
  onToggleMinimap, 
  onAddNode,
  onUndo,
  onRedo 
}) => {
  return (
    <Controls style={{ left: '50%', transform: 'translateX(-50%)' }}>
      <ControlButton onClick={onToggleLine} title={isStraightLine ? 'Switch to curved line' : 'Switch to straight line'}>
        {isStraightLine ? '—' : '~'}
      </ControlButton>
      <ControlButton onClick={onSave} title="Save flowchart">
        <SaveOutlined />
      </ControlButton>
      <ControlButton onClick={onLoad} title="Load flowchart">
        <FolderOutlined />
      </ControlButton>
      <ControlButton onClick={onAutoLayout} title="Auto Layout">
        <ReloadOutlined />
      </ControlButton>
      <ControlButton onClick={onUndo} title="Undo">
        <UndoOutlined />
      </ControlButton>
      <ControlButton onClick={onRedo} title="Redo">
        <RedoOutlined />
      </ControlButton>
      <ControlButton onClick={onToggleMinimap} title={showMinimap ? 'Hide minimap' : 'Show minimap'}>
        <GlobalOutlined />
      </ControlButton>
      <ControlButton onClick={onAddNode} title="Add Node">
        <PlusOutlined />
      </ControlButton>
    </Controls>
  );
};

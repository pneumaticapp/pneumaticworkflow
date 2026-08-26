import * as React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, { Node as ReactFlowNode } from 'reactflow';
import 'reactflow/dist/style.css';

import { ITemplateClient } from '../../../types/template';
import { EGraphNodeType, TGraphAddTaskIntent, TGraphEdge, TGraphNode } from './types';
import { useTemplateGraph } from '../../../hooks/useTemplateGraph';
import { TaskNode } from './components/TaskNode/TaskNode';
import { KickoffNode } from './components/KickoffNode/KickoffNode';
import { JunctionNode } from './components/JunctionNode/JunctionNode';
import { GraphConditionEdge } from './components/GraphConditionEdge/GraphConditionEdge';
import { applyGraphAddAffordances } from './utils/applyGraphAddAffordances';
import { applyGraphFocus } from './utils/applyGraphFocus';
import styles from './TemplateGraphEditor.css';

interface ITemplateGraphEditorProps {
  template: ITemplateClient;
  onTaskEdit: (taskApiName: string) => void;
  onKickoffEdit: () => void;
  onAddTask?: (intent: TGraphAddTaskIntent) => void;
}

const nodeTypes = {
  [EGraphNodeType.Task]: TaskNode,
  [EGraphNodeType.Kickoff]: KickoffNode,
  [EGraphNodeType.Junction]: JunctionNode,
};

const edgeTypes = {
  smoothstep: GraphConditionEdge,
};

function isCardNode(type?: string): boolean {
  return type === EGraphNodeType.Task || type === EGraphNodeType.Kickoff;
}

export const TemplateGraphEditor = ({
  template,
  onTaskEdit,
  onKickoffEdit,
  onAddTask,
}: ITemplateGraphEditorProps) => {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onNodeDrag,
    onNodeDragStop,
  } = useTemplateGraph(template);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const activeNodeId = hoveredNodeId ?? focusedNodeId;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && (focusedNodeId || hoveredNodeId)) {
        setFocusedNodeId(null);
        setHoveredNodeId(null);
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [focusedNodeId, hoveredNodeId]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: ReactFlowNode) => {
      if (!isCardNode(node.type)) {
        return;
      }

      const newFocusId = focusedNodeId === node.id ? null : node.id;
      setFocusedNodeId(newFocusId);
    },
    [focusedNodeId],
  );

  const handleNodeMouseEnter = useCallback((_: React.MouseEvent, node: ReactFlowNode) => {
    if (isCardNode(node.type)) {
      setHoveredNodeId(node.id);
    }
  }, []);

  const handleNodeMouseLeave = useCallback(() => {
    setHoveredNodeId(null);
  }, []);

  const handlePaneClick = useCallback(() => {
    setFocusedNodeId(null);
    setHoveredNodeId(null);
  }, []);

  const { nodes: affordedNodes, edges: affordedEdges } = useMemo(
    () => applyGraphAddAffordances(nodes, edges),
    [nodes, edges],
  );

  const nodesWithCallback = useMemo(
    () =>
      affordedNodes.map((node) => {
        if (node.type === EGraphNodeType.Task) {
          const canAdd = Boolean(onAddTask && node.data.addTaskIntent);

          return {
            ...node,
            data: {
              ...node.data,
              onEdit: onTaskEdit,
              onAddTask: canAdd ? onAddTask : undefined,
            },
          };
        }

        if (node.type === EGraphNodeType.Kickoff) {
          const canAdd = Boolean(onAddTask && node.data.addTaskIntent);

          return {
            ...node,
            data: {
              ...node.data,
              onEdit: onKickoffEdit,
              onAddTask: canAdd ? onAddTask : undefined,
            },
          };
        }

        return node;
      }),
    [affordedNodes, onTaskEdit, onKickoffEdit, onAddTask],
  );

  const edgesWithCallback = useMemo(
    () =>
      affordedEdges.map((edge) => {
        const canAdd = Boolean(onAddTask && edge.data?.addTaskIntent);
        if (!canAdd) {
          return edge;
        }

        return {
          ...edge,
          data: {
            ...edge.data,
            onAddTask,
          },
        };
      }),
    [affordedEdges, onAddTask],
  );

  const { nodes: displayNodes, edges: displayEdges } = useMemo(
    () => applyGraphFocus(nodesWithCallback as TGraphNode[], edgesWithCallback as TGraphEdge[], activeNodeId),
    [nodesWithCallback, edgesWithCallback, activeNodeId],
  );

  return (
    <div className={styles['template-graph-editor']} data-test-id="template-graph-editor">
      <ReactFlow
        nodes={displayNodes}
        edges={displayEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onNodeDrag={onNodeDrag}
        onNodeClick={handleNodeClick}
        onNodeMouseEnter={handleNodeMouseEnter}
        onNodeMouseLeave={handleNodeMouseLeave}
        onPaneClick={handlePaneClick}
        nodesConnectable={false}
        edgesUpdatable={false}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
};

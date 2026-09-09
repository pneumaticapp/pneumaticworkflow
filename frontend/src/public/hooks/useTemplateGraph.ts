import { useCallback, useEffect, useRef, useState } from 'react';
import {
  useNodesState,
  useEdgesState,
  applyNodeChanges,
  NodeChange,
  EdgeChange,
  Node,
  Edge,
  NodeDragHandler,
} from 'reactflow';
import { ITemplateClient } from '../types/template';
import {
  EGraphNodeType,
  TGraphNode,
  TGraphEdge,
  ITaskNodeData,
  IKickoffNodeData,
  IJunctionNodeData,
  IConditionEdgeData,
  TGraphNodePositions,
} from '../components/TemplateEdit/TemplateGraphEditor/types';
import { buildTemplateGraph } from '../components/TemplateEdit/TemplateGraphEditor/utils/buildTemplateGraph';
import { applyMovedCard } from '../components/TemplateEdit/TemplateGraphEditor/utils/routeGraph';
import {
  clearGraphNodePositions,
  getGraphNodePositions,
  hasGraphNodePositions,
  saveGraphNodePosition,
} from '../components/TemplateEdit/TemplateGraphEditor/utils/graphPositionsStorage';

type TNodeData = ITaskNodeData | IKickoffNodeData | IJunctionNodeData;

interface IUseTemplateGraphResult {
  nodes: TGraphNode[];
  edges: TGraphEdge[];
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onNodeDrag: NodeDragHandler;
  onNodeDragStop: NodeDragHandler;
  /** At least one card position is stored, so the layout differs from the automatic one. */
  hasCustomLayout: boolean;
  resetLayout: () => void;
}

export function useTemplateGraph(template: ITemplateClient): IUseTemplateGraphResult {
  const [nodes, setNodes, onNodesChange] = useNodesState<TNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<IConditionEdgeData>([]);
  const [hasCustomLayout, setHasCustomLayout] = useState(false);
  const nodesRef = useRef<TGraphNode[]>([]);
  const edgesRef = useRef<TGraphEdge[]>([]);
  const templateRef = useRef<ITemplateClient>(template);

  nodesRef.current = nodes as TGraphNode[];
  edgesRef.current = edges as TGraphEdge[];
  templateRef.current = template;

  const rebuild = useCallback(
    (storedPositions: TGraphNodePositions) => {
      const { nodes: nextNodes, edges: nextEdges } = buildTemplateGraph(templateRef.current, storedPositions);
      setNodes(nextNodes as Node<TNodeData>[]);
      setEdges(nextEdges as Edge<IConditionEdgeData>[]);
    },
    [setEdges, setNodes],
  );

  useEffect(() => {
    rebuild(getGraphNodePositions(template.id));
    setHasCustomLayout(hasGraphNodePositions(template.id));
  }, [template.id, template.tasks, template.name, template.kickoff, rebuild]);

  const resetLayout = useCallback(() => {
    clearGraphNodePositions(template.id);
    rebuild({});
    setHasCustomLayout(false);
  }, [rebuild, template.id]);

  const applyMove = useCallback(
    (movedNode: Node) => {
      if (movedNode.type === EGraphNodeType.Junction) {
        return;
      }

      const nextGraph = applyMovedCard(nodesRef.current, edgesRef.current, movedNode);
      setNodes(nextGraph.nodes as Node<TNodeData>[]);
      setEdges(nextGraph.edges as Edge<IConditionEdgeData>[]);
    },
    [setEdges, setNodes],
  );

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const dragChange = changes.find(
        (change) => change.type === 'position' && change.dragging && Boolean(change.position),
      );

      if (dragChange && dragChange.type === 'position' && dragChange.position) {
        const current = nodesRef.current.find((node) => node.id === dragChange.id);

        if (current && current.type !== EGraphNodeType.Junction) {
          const routed = applyMovedCard(nodesRef.current, edgesRef.current, {
            ...current,
            position: dragChange.position,
            dragging: true,
          });
          const rest = changes.filter((change) => change !== dragChange);

          setNodes(applyNodeChanges(rest, routed.nodes as Node<TNodeData>[]) as Node<TNodeData>[]);
          setEdges(routed.edges as Edge<IConditionEdgeData>[]);

          return;
        }
      }

      onNodesChange(changes);
    },
    [onNodesChange, setEdges, setNodes],
  );

  const onNodeDrag = useCallback<NodeDragHandler>(
    (_, movedNode) => {
      applyMove(movedNode);
    },
    [applyMove],
  );

  const onNodeDragStop = useCallback<NodeDragHandler>(
    (_, movedNode) => {
      if (movedNode.type === EGraphNodeType.Junction) {
        return;
      }

      saveGraphNodePosition(template.id, movedNode.id, movedNode.position);
      setHasCustomLayout(hasGraphNodePositions(template.id));
      applyMove(movedNode);
    },
    [applyMove, template.id],
  );

  return {
    nodes: nodes as TGraphNode[],
    edges: edges as TGraphEdge[],
    onNodesChange: handleNodesChange,
    onEdgesChange,
    onNodeDrag,
    onNodeDragStop,
    hasCustomLayout,
    resetLayout,
  };
}

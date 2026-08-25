import { useCallback, useEffect, useRef } from 'react';
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
} from '../components/TemplateEdit/TemplateGraphEditor/types';
import { buildTemplateGraph } from '../components/TemplateEdit/TemplateGraphEditor/utils/buildTemplateGraph';
import { applyMovedCard } from '../components/TemplateEdit/TemplateGraphEditor/utils/routeGraph';
import {
  getGraphNodePositions,
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
}

export function useTemplateGraph(template: ITemplateClient): IUseTemplateGraphResult {
  const [nodes, setNodes, onNodesChange] = useNodesState<TNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<IConditionEdgeData>([]);
  const nodesRef = useRef<TGraphNode[]>([]);
  const edgesRef = useRef<TGraphEdge[]>([]);

  nodesRef.current = nodes as TGraphNode[];
  edgesRef.current = edges as TGraphEdge[];

  useEffect(() => {
    const storedPositions = getGraphNodePositions(template.id);
    const { nodes: nextNodes, edges: nextEdges } = buildTemplateGraph(template, storedPositions);
    setNodes(nextNodes as Node<TNodeData>[]);
    setEdges(nextEdges as Edge<IConditionEdgeData>[]);
  }, [template.id, template.tasks, template.name, template.kickoff]);

  const applyMove = useCallback((movedNode: Node) => {
    if (movedNode.type === EGraphNodeType.Junction) {
      return;
    }

    const nextGraph = applyMovedCard(nodesRef.current, edgesRef.current, movedNode);
    setNodes(nextGraph.nodes as Node<TNodeData>[]);
    setEdges(nextGraph.edges as Edge<IConditionEdgeData>[]);
  }, [setEdges, setNodes]);

  const handleNodesChange = useCallback((changes: NodeChange[]) => {
    const dragChange = changes.find((change) => (
      change.type === 'position' && change.dragging && Boolean(change.position)
    ));

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
  }, [onNodesChange, setEdges, setNodes]);

  const onNodeDrag = useCallback<NodeDragHandler>((_, movedNode) => {
    applyMove(movedNode);
  }, [applyMove]);

  const onNodeDragStop = useCallback<NodeDragHandler>((_, movedNode) => {
    if (movedNode.type === EGraphNodeType.Junction) {
      return;
    }

    saveGraphNodePosition(template.id, movedNode.id, movedNode.position);
    applyMove(movedNode);
  }, [applyMove, template.id]);

  return {
    nodes: nodes as TGraphNode[],
    edges: edges as TGraphEdge[],
    onNodesChange: handleNodesChange,
    onEdgesChange,
    onNodeDrag,
    onNodeDragStop,
  };
}

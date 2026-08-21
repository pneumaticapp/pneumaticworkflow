import { useEffect } from 'react';
import { useNodesState, useEdgesState, NodeChange, EdgeChange, Node, Edge } from 'reactflow';
import { ITemplateClient } from '../types/template';
import {
  TGraphNode,
  TGraphEdge,
  ITaskNodeData,
  IKickoffNodeData,
  IJunctionNodeData,
  IConditionEdgeData,
} from '../components/TemplateEdit/TemplateGraphEditor/types';
import { templateToGraph } from '../components/TemplateEdit/TemplateGraphEditor/utils/templateToGraph';
import { applyDagreLayout } from '../components/TemplateEdit/TemplateGraphEditor/utils/applyDagreLayout';

type TNodeData = ITaskNodeData | IKickoffNodeData | IJunctionNodeData;

interface IUseTemplateGraphResult {
  nodes: TGraphNode[];
  edges: TGraphEdge[];
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
}

export function useTemplateGraph(template: ITemplateClient): IUseTemplateGraphResult {
  const [nodes, setNodes, onNodesChange] = useNodesState<TNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<IConditionEdgeData>([]);

  useEffect(() => {
    const { nodes: rawNodes, edges: rawEdges } = templateToGraph(template);
    const layoutedNodes = applyDagreLayout(rawNodes, rawEdges);
    setNodes(layoutedNodes as Node<TNodeData>[]);
    setEdges(rawEdges as Edge<IConditionEdgeData>[]);
  }, [template.tasks, template.name, template.kickoff]);

  return {
    nodes: nodes as TGraphNode[],
    edges: edges as TGraphEdge[],
    onNodesChange,
    onEdgesChange,
  };
}

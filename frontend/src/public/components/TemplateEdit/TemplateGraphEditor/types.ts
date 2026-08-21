import { ReactNode } from 'react';
import { Node, Edge } from 'reactflow';
import { ITemplateKickoffClient, ITemplateTaskClient } from '../../../types/template';

export enum EGraphViewMode {
  /** Linear task list. UI label is "Line". */
  List = 'list',
  Graph = 'graph',
}

export type TGraphViewModeI18nId = 'template.view-line' | 'template.view-graph';

export interface IGraphViewToggleOption {
  id: EGraphViewMode;
  labelId: TGraphViewModeI18nId;
}

export const GRAPH_VIEW_TOGGLE_OPTIONS: IGraphViewToggleOption[] = [
  { id: EGraphViewMode.List, labelId: 'template.view-line' },
  { id: EGraphViewMode.Graph, labelId: 'template.view-graph' },
];

export enum EGraphNodeType {
  Kickoff = 'kickoff',
  Task = 'task',
  Junction = 'junction',
}

export type TJunctionKind = 'fork' | 'join';

export interface IConnectedHandles {
  hasTargetTop: boolean;
  hasSourceBottom: boolean;
  hasSourceSkip: boolean;
  hasTargetSkip: boolean;
}

export interface ITaskNodeData {
  task: ITemplateTaskClient;
  isSelected: boolean;
  onEdit: (apiName: string) => void;
  handles?: IConnectedHandles;
}

export interface IKickoffNodeData {
  kickoff: ITemplateKickoffClient;
  templateName: string;
  onEdit?: () => void;
  handles?: IConnectedHandles;
}

export interface IJunctionNodeData {
  kind: TJunctionKind;
}

export type TTaskNode = Node<ITaskNodeData, EGraphNodeType.Task>;
export type TKickoffNode = Node<IKickoffNodeData, EGraphNodeType.Kickoff>;
export type TJunctionNode = Node<IJunctionNodeData, EGraphNodeType.Junction>;
export type TGraphNode = TTaskNode | TKickoffNode | TJunctionNode;

export interface IConditionEdgeData {
  summary?: string;
  isConditional?: boolean;
}

export type TGraphEdge = Edge<IConditionEdgeData>;

export interface IGraphState {
  nodes: TGraphNode[];
  edges: TGraphEdge[];
}

export interface ITemplateGraphViewState {
  viewMode: EGraphViewMode;
  selectedTaskApiName: string | null;
}

export interface IGraphTaskEditorPanelProps {
  children: ReactNode;
  onClose: () => void;
}

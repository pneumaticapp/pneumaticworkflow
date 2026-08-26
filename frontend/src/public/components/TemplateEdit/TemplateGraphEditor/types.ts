import { ReactNode } from 'react';
import { Node, Edge } from 'reactflow';
import { ITemplateKickoffClient, ITemplateTaskClient } from '../../../types/template';
import { EConditionLogicOperations, EConditionOperators } from '../TaskForm/Conditions';

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

export interface IGraphNodePosition {
  x: number;
  y: number;
}

export type TGraphNodePositions = Record<string, IGraphNodePosition>;
export type TGraphPositionsStorage = Record<string, TGraphNodePositions>;

export type TJunctionKind = 'fork' | 'join';

export interface IConnectedHandles {
  hasTargetTop: boolean;
  hasTargetBottom: boolean;
  hasTargetLeft: boolean;
  hasTargetRight: boolean;
  hasSourceTop: boolean;
  hasSourceBottom: boolean;
  hasSourceLeft: boolean;
  hasSourceRight: boolean;
}

export type TGraphAddTaskKind = 'continue' | 'insert';

export interface IGraphContinueTaskIntent {
  kind: Extract<TGraphAddTaskKind, 'continue'>;
  afterId: string;
}

export interface IGraphInsertTaskIntent {
  kind: Extract<TGraphAddTaskKind, 'insert'>;
  afterId: string;
  beforeId: string;
}

export type TGraphAddTaskIntent = IGraphContinueTaskIntent | IGraphInsertTaskIntent;

export interface IGraphNewTaskDraft {
  name: string;
  number: number;
  conditions: ITemplateTaskClient['conditions'];
}

export interface ITaskNodeData {
  task: ITemplateTaskClient;
  isSelected: boolean;
  onEdit: (apiName: string) => void;
  handles?: IConnectedHandles;
  addTaskIntent?: TGraphAddTaskIntent;
  onAddTask?: (intent: TGraphAddTaskIntent) => void;
}

export interface IKickoffNodeData {
  kickoff: ITemplateKickoffClient;
  templateName: string;
  onEdit?: () => void;
  handles?: IConnectedHandles;
  addTaskIntent?: TGraphAddTaskIntent;
  onAddTask?: (intent: TGraphAddTaskIntent) => void;
}

export interface IJunctionNodeData {
  kind: TJunctionKind;
}

export type TTaskNode = Node<ITaskNodeData, EGraphNodeType.Task>;
export type TKickoffNode = Node<IKickoffNodeData, EGraphNodeType.Kickoff>;
export type TJunctionNode = Node<IJunctionNodeData, EGraphNodeType.Junction>;
export type TGraphNode = TTaskNode | TKickoffNode | TJunctionNode;

export type TGraphEdgePathKind = 'straight' | 'from-task' | 'from-fork' | 'skip';

/** Visual kind of a line: gray solid start-after, or orange dashed check-if. */
export type TGraphEdgeLine = 'solid' | 'dashed';

export type TGraphEdgeFocus = 'highlighted' | 'dimmed';

export interface IGraphEdgeAnchor {
  x: number;
  y: number;
}

/** One Check If predicate shown on a dashed edge tooltip. */
export interface IGraphConditionClause {
  fieldLabel: string;
  operator: EConditionOperators | null;
  value?: string;
  logicOperation?: EConditionLogicOperations;
}

export interface IConditionEdgeData {
  summary?: string;
  isConditional?: boolean;
  /** Check If predicates for the tooltip; formatted in `ConditionEdgeInfo`. */
  clauses?: IGraphConditionClause[];
  /** Labels of the cards the task starts after. `KICKOFF_START_AFTER` means the kick-off form. */
  startAfter?: string[];
  pathKind?: TGraphEdgePathKind;
  /** Side-lane X for a skip around a column, or the tree gutter a fork branch turns in. */
  laneX?: number;
  /** Row-gap Y used with a gutter turn when the destination row would run under a card. */
  laneY?: number;
  /** Which side a detour uses when it must leave the column. */
  laneSide?: 'left' | 'right';
  /** The line runs in a side lane instead of the vertical stem, so it never joins a junction. */
  isLaneRouted?: boolean;
  /** Flow-space point on the source card face. The SVG path uses this instead of React Flow handleBounds. */
  sourceAnchor?: IGraphEdgeAnchor;
  /** Flow-space point on the target card face. */
  targetAnchor?: IGraphEdgeAnchor;
  /** Handle ids used to build the path; preferred over React Flow's live handleBounds. */
  sourceHandle?: string;
  targetHandle?: string;
  /** Perpendicular run off a card before the first turn. Junctions stay 0. */
  sourceStandoff?: number;
  /** Perpendicular run into a card after the last turn. Junctions stay 0. */
  targetStandoff?: number;
  /** Focus state assigned by `applyGraphFocus`; drives the label appearance. */
  focus?: TGraphEdgeFocus;
  /** Insert-between intent for a unique gray stem; stamped by `applyGraphAddAffordances`. */
  addTaskIntent?: TGraphAddTaskIntent;
  onAddTask?: (intent: TGraphAddTaskIntent) => void;
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

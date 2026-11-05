import type { CatalogTool, ToolDef, Toolset } from '../mcp/toolDef.js';
import { accountTools } from './accounts.js';
import { analyticsTools } from './analytics.js';
import { datasetReadTools, datasetTools } from './datasets.js';
import { designerTools } from './designer.js';
import { fileTools } from './files.js';
import { libraryTools } from './library.js';
import { peopleTools } from './people.js';
import { reportTools } from './reports.js';
import { taskTools } from './tasks.js';
import { templateTools } from './templates.js';
import { workflowTools } from './workflows.js';

const inToolset = (toolset: Toolset, tools: readonly ToolDef[]): CatalogTool[] =>
  tools.map((definition) => ({ ...definition, toolset }));

export const allTools: readonly CatalogTool[] = [
  ...inToolset('core', accountTools),
  ...inToolset('admin', peopleTools),
  ...inToolset('core', templateTools),
  ...inToolset('design', designerTools),
  ...inToolset('design', libraryTools),
  ...inToolset('core', workflowTools),
  ...inToolset('core', taskTools),
  ...inToolset('files', fileTools),
  ...inToolset('analytics', reportTools),
  ...inToolset('analytics', analyticsTools),
  ...inToolset('core', datasetReadTools),
  ...inToolset('admin', datasetTools),
];

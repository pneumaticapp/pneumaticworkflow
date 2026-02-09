import type { TextMatchTransformer } from '@lexical/markdown';

import { variableRegex } from '../../../../constants/defaultValues';
import { VariableNode, $createVariableNode, $isVariableNode } from '../nodes/VariableNode';
import type { TTaskVariable } from '../../../TemplateEdit/types';



const variableImportRegex = variableRegex;

export function createVariableTransformer(
  templateVariables?: TTaskVariable[],
): TextMatchTransformer {
  return {
    dependencies: [VariableNode],
    export: (node) =>
      $isVariableNode(node) ? `{{${node.getApiName()}}}` : null,
    importRegExp: variableImportRegex,
    regExp: variableImportRegex,
    replace: (textNode, match) => {
      const apiName = match[1];
      const variable = templateVariables?.find(
        (v) => v.apiName === apiName,
      );
      const node = $createVariableNode({
        apiName: variable?.apiName ?? apiName,
        title: variable?.title ?? apiName,
        subtitle: variable?.subtitle,
      });
      textNode.replace(node);
    },
    type: 'text-match',
  };
}

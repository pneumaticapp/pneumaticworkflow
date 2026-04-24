import { variableRegex } from '../../../../constants/defaultValues';
import { TTaskVariable } from '../../types';
import { getLocalizedSystemVariable, isSystemVariable } from './getTaskVariables';

export type TSubtitleSegment =
  | { type: 'text'; value: string; id: string }
  | { type: 'variable'; title: string; id: string };

export const getFormattedSubtitleSegments = (
  subtitle: string,
  variables: TTaskVariable[],
  formatMessage?: any,
): TSubtitleSegment[] => {
  const replaceRegex = new RegExp(variableRegex, 'gi');
  const segments: TSubtitleSegment[] = [];
  let lastIndex = 0;
  let id = 0;
  let match = replaceRegex.exec(subtitle);
  while (match !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', value: subtitle.slice(lastIndex, match.index), id: `t-${id}` });
      id += 1;
    }
    const apiName = match[1];
    const item = variables.find((elem) => elem.apiName === apiName);
    
    let segmentTitle = item?.title ?? match[0];
    if (formatMessage && isSystemVariable(apiName)) {
      segmentTitle = getLocalizedSystemVariable({
        apiName,
        title: segmentTitle,
        formatMessage,
      }).title;
    }

    segments.push({ type: 'variable', title: segmentTitle, id: `v-${id}` });
    id += 1;
    lastIndex = replaceRegex.lastIndex;
    match = replaceRegex.exec(subtitle);
  }
  if (lastIndex < subtitle.length) {
    segments.push({ type: 'text', value: subtitle.slice(lastIndex), id: `t-${id}` });
  }
  return segments.length > 0 ? segments : [{ type: 'text', value: subtitle, id: 't-0' }];
};

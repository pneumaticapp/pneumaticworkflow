import { variableRegex } from '../../../../constants/defaultValues';
import { TTaskVariable } from '../../types';

export const getFormattedSubtitle = (subtitle: string, variables: TTaskVariable[]): string => {
  const replaceRegex = new RegExp(variableRegex, 'gi');
  return subtitle.replace(replaceRegex, (match, apiName) => {
    const item = variables.find((elem) => elem.apiName === apiName);
    return item ? `<span class={style['var']}>${item.title}</span>` : match;
  });
};

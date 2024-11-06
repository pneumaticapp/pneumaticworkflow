import { TChecklistItemData } from '../../components/RichEditor/utils/checklistsPlugin/types';
import { TOutputChecklist } from '../../types/template';

export type TInputTChecklistItemData = {
  value: string;
} & TChecklistItemData;

export const prepareChecklistsForAPI = (markdown: string): TOutputChecklist[] => {
  const extractedChecklist = extractChecklistsFromMarkdown(markdown);

  const outputChecklists = [] as TOutputChecklist[];
  let state: 'list-added' | 'item-added' = 'list-added';
  let currentList = {} as TOutputChecklist;

  extractedChecklist.forEach(({ listApiName, itemApiName, value }, index) => {
    if (state === 'list-added') {
      currentList = {
        apiName: listApiName,
        selections: [],
      };
    }

    currentList.selections.push({
      apiName: itemApiName,
      value,
    });
    state = 'item-added';

    const isLastItem =
      index === extractedChecklist.length - 1 || currentList.apiName !== extractedChecklist[index + 1].listApiName;
    if (isLastItem) {
      outputChecklists.push(currentList);
      state = 'list-added';
    }
  });

  return outputChecklists;
};

export function extractChecklistsFromMarkdown(markdown: string): TInputTChecklistItemData[] {
  const regEx = /\[clist:([\w-]+)\|([\w-]+)\](.*)?(?=\[\/clist])\[\/clist]/g;

  return [...markdown.matchAll(regEx)].map(match => {
    const [, listApiName, itemApiName, value = ''] = match;

    return {
      listApiName,
      itemApiName,
      value,
    }
  })
}

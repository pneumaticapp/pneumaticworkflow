import { ContentState, convertToRaw } from 'draft-js';

export function logDraftContent(content: ContentState) {
  console.log(JSON.stringify(convertToRaw(content) , null, 2));
}

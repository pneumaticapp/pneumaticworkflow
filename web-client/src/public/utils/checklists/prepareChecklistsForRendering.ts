export const prepareChecklistsForRendering = (initialText: string) => {
  const regEx = /(.*\n?)(\[clist:[\w-]+\|[\w-]+\])/g;

  const result = initialText.replace(regEx, (match, prevLine, checkOpening) => {
    if (!prevLine?.trim() || prevLine.includes('[/clist]')) {
      return match;
    }
  
    return `${prevLine}\n${checkOpening}`;
  });

  return result;
}

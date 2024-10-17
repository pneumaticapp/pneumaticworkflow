export function createCheckPlaceholderId(listApiName: string, itemApiName: string) {
  return `clist_${listApiName}_${itemApiName}`;
}

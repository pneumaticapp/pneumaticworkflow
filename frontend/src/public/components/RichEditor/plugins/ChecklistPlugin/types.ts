export type InsertParagraphFromEmptyChecklistPayload = {
  itemKey: string;
  parentKey: string;
  nextSiblingKeys: string[];
};

export type BackspaceOnEmptyChecklistPayload = {
  itemKey: string;
  parentKey: string | null;
  prevItemKey: string | null;
};

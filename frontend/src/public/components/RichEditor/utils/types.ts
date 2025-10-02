export enum ECustomEditorEntities {
  File = 'file',
  Image = 'image',
  Video = 'video',
  Variable = 'variable',
  Mention = 'mention',
  Link = 'LINK',
}

export const CUSTOM_EDITOR_ENTITES = Object.values(ECustomEditorEntities);

export type TEditorAttachment = {
  url: string;
  id?: number;
  name?: string;
};

export enum EEditorBlock {
  Unstyled  = 'unstyled',
  HeaderOne = 'header-one',
  HeaderTwo = 'header-two',
  HeaderThree = 'header-three',
  HeaderFour = 'header-four',
  HeaderFive = 'header-five',
  HeaderSix = 'header-six',
  UnorderedListItem = 'unordered-list-item',
  OrderedListItem = 'ordered-list-item',
  Blockquote = 'blockquote',
  Code = 'code-block',
  Atomic = 'atomic',
};

export enum EEditorStyle {
  Bold = 'BOLD',
  Italic = 'ITALIC',
};

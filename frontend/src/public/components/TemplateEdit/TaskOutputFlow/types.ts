export interface IFieldsetEditorTitleProps {
  apiNameBinding: string;
  title: string;
  onEditFieldsetTitle: (apiNameBinding: string, title: string) => void;
  formatMessage: (descriptor: { id: string }) => string;
}

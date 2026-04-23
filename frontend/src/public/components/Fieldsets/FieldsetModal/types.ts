export enum EFieldsetModalType {
  Create = 'create',
  Edit = 'edit',
}

export interface IFieldsetModalProps {
  type: EFieldsetModalType;
  templateId?: number;
}

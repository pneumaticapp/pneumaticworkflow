export enum EDatasetModalType {
  Create = 'create',
  Edit = 'edit',
}

export interface IDatasetModalProps {
  type: EDatasetModalType;
}

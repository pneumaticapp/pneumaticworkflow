import { ETemplateOwnerType } from "../../types/template";

export interface IUserDataWithGroupProps {
  type: ETemplateOwnerType;
  idItem: number;
  children(user: any): React.ReactNode;
}

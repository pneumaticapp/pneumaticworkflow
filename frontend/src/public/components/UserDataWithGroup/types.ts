import { ETaskPerformerType, ETemplateOwnerType } from "../../types/template";

export interface IUserDataWithGroupProps {
  type: ETemplateOwnerType | ETaskPerformerType.AiAgent;
  idItem: number;
  children(user: any): React.ReactNode;
}

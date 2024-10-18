import { IAuthUser } from '../../../../types/redux';
import { IWorkflowTemplate } from '../../../../types/workflow';

export function checkCanControlWorkflow(currentUser: IAuthUser, template: IWorkflowTemplate | null) {
  const { id: currentUserId, isAccountOwner, isAdmin } = currentUser;

  if (isAccountOwner) {
    return true;
  }

  const isTemplateOwner = template?.templateOwners?.some((id) => id === currentUserId);

  return isTemplateOwner && isAdmin;
}

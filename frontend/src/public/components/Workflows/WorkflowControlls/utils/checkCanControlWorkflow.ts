import { IAuthUser } from '../../../../types/redux';

export function checkCanControlWorkflow(currentUser: IAuthUser, owners: number[]) {
  const { id: currentUserId, isAccountOwner, isAdmin } = currentUser;

  if (isAccountOwner) {
    return true;
  }

  const isTemplateOwner = owners.some((id) => id === currentUserId);

  return isTemplateOwner && isAdmin;
}

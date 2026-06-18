import { ERoutes } from '../../constants/routes';

// TODO: templateId parameter kept for backward compatibility — will be removed in Flow 3
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function getLinkToFieldsets(_templateId: number) {
  return ERoutes.Fieldsets;
}

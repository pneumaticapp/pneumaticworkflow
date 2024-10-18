import { commonRequest } from './commonRequest';

export function discardTemplateChanges({ templateId }: { templateId: Number }) {
  const url = '/templates/:id/discard-changes'.replace(':id', String(templateId));

  return commonRequest(
    url,
    { method: 'POST' },
    { shouldThrow: true, responseType: 'empty' },
  );
}

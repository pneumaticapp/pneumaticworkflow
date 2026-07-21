import { ITemplateClient } from '../../../types/template';
import { haveSameKickoffFields } from '../../../utils/template';
import { getChangedFields } from './templateFormUtils';

// Keep in sync with `patchTemplateSaga` in redux/template/saga.ts. The saga
// flips `isActive` to false server-side whenever a non-activation field changes
// and only reflects it back to Formik via a Redux `setTemplate` reinitialize.
// `applyImmediateDeactivation` mirrors that decision in the wrapped setters so
// Formik (and controls like `RouteLeavingGuard` that read from it) deactivate
// on the same tick as the edit instead of waiting for the deferred persist flush.
const NON_DEACTIVATIVE_FIELDS: (keyof ITemplateClient)[] = ['isActive', 'isPublic', 'publicUrl'];

function shouldDeactivateTemplate(
  changedFields: Partial<ITemplateClient>,
  previousTemplate: ITemplateClient,
): boolean {
  if (changedFields.isActive === true) {
    return false;
  }

  let shouldDeactivate = Object.keys(changedFields).some(
    (key) => !NON_DEACTIVATIVE_FIELDS.includes(key as keyof ITemplateClient),
  );

  if (Object.keys(changedFields).length === 1 && Object.prototype.hasOwnProperty.call(changedFields, 'kickoff')) {
    const kickoffChanged = changedFields.kickoff;
    const previousKickoff = previousTemplate.kickoff;

    if (haveSameKickoffFields(kickoffChanged?.fields, previousKickoff.fields)) {
      shouldDeactivate =
        kickoffChanged?.description === previousKickoff.description ? shouldDeactivate : false;
    }
  }

  return shouldDeactivate;
}

export function applyImmediateDeactivation(previous: ITemplateClient, next: ITemplateClient): ITemplateClient {
  if (!previous.isActive) {
    return next;
  }

  const changedFields = getChangedFields(previous, next);

  if (shouldDeactivateTemplate(changedFields, previous)) {
    return { ...next, isActive: false };
  }

  return next;
}

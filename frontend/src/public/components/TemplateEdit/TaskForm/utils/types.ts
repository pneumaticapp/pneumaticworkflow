import type { IFieldsetBindingClient } from '../../../../types/fieldset';
import type { ITemplateKickoffClient, ITemplateTaskClient, TTemplateFieldFieldset } from '../../../../types/template';

export interface IGetLocalizedSystemVariableParams {
  apiName: string;
  title: string;
  subtitle?: string;
  formatMessage: (descriptor: { id: string }) => string;
}

export interface IGetLocalizedSystemVariableReturn {
  title: string;
  subtitle?: string;
}

export type TGetVariablesParam = {
  kickoff: Pick<ITemplateKickoffClient, 'fields'> & { fieldsets?: (IFieldsetBindingClient | TTemplateFieldFieldset)[] };
  tasks: (Pick<ITemplateTaskClient, 'fields' | 'apiName'> & {
    name?: ITemplateTaskClient['name'];
    fieldsets?: (IFieldsetBindingClient | TTemplateFieldFieldset)[];
  })[];
  templateId?: number;
};

export type TSubtitleSegment =
  { type: 'text'; value: string; id: string } | { type: 'variable'; title: string; id: string };

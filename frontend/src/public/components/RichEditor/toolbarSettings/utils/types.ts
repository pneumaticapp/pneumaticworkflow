import { ToolbarChildrenProps } from '@draft-js-plugins/static-toolbar/lib/components/Toolbar';

export interface IExtendedToolbarChildrenProps extends ToolbarChildrenProps {
  theme: {
    isModal?: boolean;
    button?: string;
    active?: string;
    buttonWrapper?: string;
  };
}

/* eslint-disable */
/* prettier-ignore */
// tslint:disable: match-default-export-name max-file-line-count
import * as React from 'react';
import classnames from 'classnames';
import { EditorState, ContentState, EditorProps, getDefaultKeyBinding, RichUtils, ContentBlock } from 'draft-js';
import Editor, { composeDecorators } from '@draft-js-plugins/editor';
import createAttachmentPlugin from './utils/AttachmentsPlugin';
import createLinkifyPlugin from '@draft-js-plugins/linkify';
import createMentionPlugin from 'draft-js-mention-plugin';
import createFocusPlugin from '@draft-js-plugins/focus';
import positionSuggestions from 'draft-js-mention-plugin/lib/utils/positionSuggestions';
import createToolbarPlugin from '@draft-js-plugins/static-toolbar';
import createLinkPlugin from './utils/linksPlugin';
import createCheckableListPlugin from './utils/checklistsPlugin';

import { Desktop, Mobile } from '../media';

import { Image } from './utils/AttachmentsPlugin/Image';
import { File } from './utils/AttachmentsPlugin/File';
import { Video } from './utils/AttachmentsPlugin/Video';
import { removeBlock } from './utils/removeBlock';
import { stripUnsupportedStyles } from './utils/stripUnsupportedStyles';
import { getSuggestionByValue } from './utils/getSuggestionByValue';
import { handlePressTab } from './utils/handlePressTab';
import { trackAddVideo } from './utils/trackAddVideo';
import { convertDraftToText, getInitialEditorState } from './utils/сonverters';
import { handlePasteAttachments } from './utils/handlePasteAttachments';
import { removeOrphanedEntities } from './utils/removeOrphanedEntities';
import {
  BoldButton,
  ItalicButton,
  OrderedListButton,
  UnorderedListButton,
  ImageAttachmentButton,
  VideoAttachmentButton,
  FileAttachmentButton,
  Separator,
  toolbarConfig,
} from './toolbarSettings';
import { ENTER_KEY_CODE } from '../../constants/defaultValues';
import { Loader } from '../UI';
import { IntlMessages } from '../IntlMessages';

import { handleUploadAttachments } from './utils/handleUploadAttachments';
import { deleteAttachment } from '../../api/deleteAttachment';
import { TEditorAttachment } from './utils/types';
import { setChecklistApiNames } from './utils/checklistsPlugin/setChecklistApiNames';
import { prepareChecklistsForAPI } from '../../utils/checklists/prepareChecklistsForAPI';
import { TOutputChecklist } from '../../types/template';
import { shouldHidePlaceholder } from './utils/shouldHidePlaceholder';
import { TForegroundColor } from '../UI/Fields/common/types';
import { getForegroundClass } from '../UI/Fields/common/utils/getForegroundClass';

import styles from './RichEditor.css';
import mentionsStyles from './MentionStyles.css';
import focusStyles from './FocusStyles.css';
import 'draft-js/dist/Draft.css';

enum EEditorKeyCommand {
  Enter = 'enter',
}

export type TMentionData = {
  id?: number;
  name: string;
  link?: string;
};

export interface IPositionSuggestionsParams {
  decoratorRect: { x: number; y: number } & ClientRect;
  popover: HTMLElement;
  props: {
    open: boolean;
    suggestions: TMentionData[];
  };
  // tslint:disable-next-line: no-any
  state: any;
}

export interface IRichEditorState {
  isLoading: boolean;
  shouldSubmitAfterFileLoaded: boolean;
  editorState: EditorState;
  suggestions: TMentionData[];
  areSuggestionsOpened: boolean;
}

export interface IRichEditorProps {
  accountId: number;
  mentions: TMentionData[];
  placeholder: EditorProps['placeholder'];
  className?: string;
  defaultValue?: string;
  initialState?: EditorState;
  withMentions?: boolean;
  withToolbar?: boolean;
  withChecklists?: boolean;
  multiline?: boolean;
  children?: React.ReactNode;
  title?: string;
  decorators?: React.ComponentProps<typeof Editor>['decorators'];
  foregroundColor?: TForegroundColor;

  submitIcon?: React.ReactNode;
  cancelIcon?: React.ReactNode;

  handleChange(value: string): Promise<string>;
  handleChangeChecklists?(checklists: TOutputChecklist[]): void;
  onSubmit?(): void;
  onCancel?(): void;
}

export class RichEditor extends React.Component<IRichEditorProps, IRichEditorState> {
  public state: IRichEditorState = {
    isLoading: false,
    shouldSubmitAfterFileLoaded: false,
    editorState: this.props.initialState || getInitialEditorState(this.props.defaultValue),
    suggestions: this.props.mentions,
    areSuggestionsOpened: false,
  };

  private toolbarPlugin: ReturnType<typeof createToolbarPlugin>;
  private linkifyPlugin: ReturnType<typeof createLinkifyPlugin>;
  private focusPlugin: ReturnType<typeof createFocusPlugin>;
  private attachmentPlugin: ReturnType<typeof createAttachmentPlugin>;
  private linkPlugin: ReturnType<typeof createLinkPlugin>;
  private checkableListPlugin = createCheckableListPlugin();

  public static defaultProps: Partial<IRichEditorProps> = {
    withMentions: true,
    withToolbar: true,
  };

  private deleteAttachment = (block: ContentBlock) => {
    const { id } = this.state.editorState
      .getCurrentContent()
      .getEntity(block.getEntityAt(0))
      .getData() as TEditorAttachment;

    if (id) {
      deleteAttachment(id);
    }

    this.onChange(removeBlock(this.state.editorState, block.getKey()));
  };

  public constructor(props: IRichEditorProps) {
    super(props);
    this.linkifyPlugin = createLinkifyPlugin();
    this.linkPlugin = createLinkPlugin();
    this.toolbarPlugin = createToolbarPlugin(toolbarConfig);
    this.focusPlugin = createFocusPlugin({
      theme: {
        focused: focusStyles['focused'],
        unfocused: focusStyles['unfocused'],
      },
    });
    this.attachmentPlugin = createAttachmentPlugin({
      imageComponent: (props) => <Image {...props} deleteAttachment={this.deleteAttachment} />,
      fileComponent: (props) => <File {...props} deleteAttachment={this.deleteAttachment} />,
      videoComponent: (props) => <Video {...props} deleteAttachment={this.deleteAttachment} />,
      decorator: composeDecorators(this.focusPlugin.decorator),
    });
  }

  public componentDidMount() {
    if (!this.editorContainer.current) {
      return;
    }

    this.editorContainer.current.onpaste = (e) =>
      handlePasteAttachments(
        e,
        this.props.accountId,
        this.state.editorState,
        this.attachmentPlugin.addAttachment,
        () => this.setState({ isLoading: true }),
        async (newState) => {
          await this.onChange(newState);
          this.setState({ isLoading: false });
        },
      );
  }

  public componentDidUpdate(prevProps: IRichEditorProps, prevState: IRichEditorState) {
    const { isLoading: prevIsLoading } = prevState;
    const { isLoading, shouldSubmitAfterFileLoaded } = this.state;
    const loadingStarted = !prevIsLoading && isLoading;
    const loadingFinished = prevIsLoading && !isLoading;

    if (loadingFinished && shouldSubmitAfterFileLoaded) {
      this.handleSubmit();
    }

    if (!this.editorContainer.current) {
      return;
    }
    if (loadingStarted) {
      this.editorContainer.current.onkeydown = () => false;
    }
    if (loadingFinished) {
      this.editorContainer.current.onkeydown = null;
    }
  }

  public componentDidCatch() {
    this.forceUpdate();
  }

  private handleSubmit = () => {
    const { onSubmit } = this.props;
    const { isLoading } = this.state;

    if (!onSubmit) {
      return;
    }

    if (isLoading) {
      this.setState({ shouldSubmitAfterFileLoaded: true });

      return;
    }

    onSubmit();
    this.setState({ shouldSubmitAfterFileLoaded: false }, this.resetEditor);
  };

  private handleCancel = () => {
    const { onCancel } = this.props;
    const { isLoading } = this.state;

    if (!onCancel) {
      return;
    }

    if (isLoading) {
      this.setState({ shouldSubmitAfterFileLoaded: true });

      return;
    }

    onCancel();
    this.setState({ shouldSubmitAfterFileLoaded: false }, this.resetEditor);
  };

  private customPositionSuggestions = ({ decoratorRect, popover, state, props }: IPositionSuggestionsParams) => {
    const { left, ...restProps } = positionSuggestions({ decoratorRect, popover, state, props });

    const editorWidth = this.editorContainer.current!.offsetWidth;
    const popoverWitdh = popover.offsetWidth;

    const newLeft = parseFloat(left) + popoverWitdh > editorWidth ? `${editorWidth - popoverWitdh}px` : left;

    return { left: newLeft, ...restProps };
  };

  private mentionPlugin = createMentionPlugin({
    mentionTrigger: '@',
    entityMutability: 'IMMUTABLE',
    // supportWhitespace: true causes bug when popover is not triggering immediately
    supportWhitespace: false,
    mentionPrefix: '@',
    theme: mentionsStyles,
    positionSuggestions: this.customPositionSuggestions,
  });
  public editorContainer = React.createRef<HTMLDivElement>();
  private editor = React.createRef<Editor>();

  public onChange = async (nextState: EditorState) => {
    const { handleChange, handleChangeChecklists, withChecklists, multiline = true } = this.props;
    const { editorState } = this.state;

    const normalizedNextState = removeOrphanedEntities(stripUnsupportedStyles(nextState, editorState));
    const prevContent = editorState.getCurrentContent();
    const newContent = normalizedNextState.getCurrentContent();

    if (!multiline && newContent.getPlainText().indexOf('\n') !== -1) {
      return;
    }

    this.setState({ editorState: normalizedNextState });

    if (prevContent === newContent) {
      return;
    }

    const stateWithChecklists = setChecklistApiNames(normalizedNextState);
    const contentWithChecklists = stateWithChecklists.getCurrentContent();
    this.setState({ editorState: stateWithChecklists });

    const plainText = convertDraftToText(contentWithChecklists);

    if (withChecklists && handleChangeChecklists) {
      const apiChecklists = prepareChecklistsForAPI(plainText);
      handleChangeChecklists(apiChecklists);
    }

    await handleChange(plainText);
  };

  private onSearchChange = ({ value }: { value: string }) => {
    const { mentions } = this.props;

    this.setState({
      suggestions: getSuggestionByValue(value, mentions),
    });
  };

  public focus = () => {
    this.editor.current?.focus();
  };

  public resetEditor = () => {
    const editorState = EditorState.push(this.state.editorState, ContentState.createFromText(''), 'remove-range');
    const focusedEditorState = EditorState.moveFocusToEnd(editorState);
    this.setState({ editorState: focusedEditorState });
  };

  private customKeyBindingFn = (e: React.KeyboardEvent) => {
    if (e.keyCode === ENTER_KEY_CODE && (e.ctrlKey || e.metaKey)) {
      return EEditorKeyCommand.Enter;
    }

    return getDefaultKeyBinding(e);
  };

  private handleKeyCommand = (command: EEditorKeyCommand) => {
    const { onSubmit } = this.props;
    enum ECommandState {
      Handled = 'handled',
      NotHandled = 'not-handled',
    }

    if (command === EEditorKeyCommand.Enter && onSubmit) {
      this.handleSubmit();

      return ECommandState.Handled;
    }

    const newState = RichUtils.handleKeyCommand(this.state.editorState, command);

    if (newState) {
      this.onChange(newState);

      return ECommandState.Handled;
    }

    return ECommandState.NotHandled;
  };

  private handlePastedText = (text: string) => {
    trackAddVideo(text);

    return false;
  };

  private uploadAttachments = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const { accountId } = this.props;

    await handleUploadAttachments(
      e,
      accountId,
      this.state.editorState,
      this.attachmentPlugin.addAttachment,
      () => this.setState({ isLoading: true }),
      async (newState) => {
        await this.onChange(newState);
        this.setState({ isLoading: false });
      },
      () => this.setState({ isLoading: false }),
    );
  };

  public render() {
    const {
      className,
      withChecklists,
      withMentions,
      withToolbar,
      title,
      decorators,
      children,
      submitIcon,
      cancelIcon,
      multiline = true,
      foregroundColor = 'white',
      onSubmit,
      onCancel,
    } = this.props;
    const { areSuggestionsOpened, isLoading, shouldSubmitAfterFileLoaded, editorState } = this.state;
    const { MentionSuggestions } = this.mentionPlugin;
    const { Toolbar } = this.toolbarPlugin;
    const { LinkButton, AddLinkForm } = this.linkPlugin;
    const { ChecklistButton } = this.checkableListPlugin;

    const hidePlaceholder = shouldHidePlaceholder(editorState);
    const plugins = [
      this.checkableListPlugin,
      this.linkifyPlugin,
      this.focusPlugin,
      this.attachmentPlugin,
      this.linkPlugin,
      withMentions && this.mentionPlugin,
      withToolbar && this.toolbarPlugin,
    ].filter(Boolean);

    const withControls = Boolean(onSubmit);

    return (
      <div
        className={classnames(
          styles['editor-wrapper'],
          title && styles['editor-wrapper_with-title'],
          hidePlaceholder && styles['editor-wrapper_hide-placeholder'],
        )}
      >
        {title && <span className={classnames(styles['title'], getForegroundClass(foregroundColor))}>{title}</span>}
        <div
          ref={this.editorContainer}
          className={classnames(
            styles['editor'],
            isLoading && styles['editor_loading'],
            multiline && styles['editor_multiline'],
            styles['editor-common'],
            className,
          )}
          onClick={this.focus}
        >
          <Loader isLoading={isLoading} />
          <Editor
            ref={this.editor}
            editorState={this.state.editorState}
            onChange={this.onChange}
            plugins={plugins}
            handleKeyCommand={this.handleKeyCommand}
            keyBindingFn={!areSuggestionsOpened ? this.customKeyBindingFn : undefined}
            onTab={(event) => handlePressTab(event, this.state.editorState, this.onChange)}
            // @ts-ignore
            handlePastedText={this.handlePastedText}
            decorators={decorators}
            {...this.props}
          />
          {withMentions && (
            <MentionSuggestions
              onSearchChange={this.onSearchChange}
              suggestions={this.state.suggestions}
              onOpen={() => this.setState({ areSuggestionsOpened: true })}
              onClose={() => this.setState({ areSuggestionsOpened: false })}
            />
          )}
          <div className={styles['controls-wrapper']}>
            {withToolbar && (
              <>
                <Desktop>
                  <Toolbar>
                    {(externalProps) => (
                      <>
                        <BoldButton {...externalProps} />
                        <ItalicButton {...externalProps} />
                        <OrderedListButton {...externalProps} />
                        <UnorderedListButton {...externalProps} />
                        <LinkButton {...externalProps} />
                        {withChecklists && <ChecklistButton />}
                        <Separator />
                        <ImageAttachmentButton {...externalProps} uploadAttachments={this.uploadAttachments} />
                        <VideoAttachmentButton {...externalProps} uploadAttachments={this.uploadAttachments} />
                        <FileAttachmentButton {...externalProps} uploadAttachments={this.uploadAttachments} />
                      </>
                    )}
                  </Toolbar>
                </Desktop>
                <Mobile>
                  <Toolbar>
                    {(externalProps) => (
                      <FileAttachmentButton {...externalProps} uploadAttachments={this.uploadAttachments} />
                    )}
                  </Toolbar>
                </Mobile>
              </>
            )}
            {withControls && (
              <div className={styles['actions']}>
                <div className={styles['controls']}>
                  {onCancel && (
                    <>
                      <button
                        className={classnames('cancel-button', styles['controls__send-button'])}
                        onClick={this.handleCancel}
                        disabled={shouldSubmitAfterFileLoaded}
                      >
                        {cancelIcon ? cancelIcon : <IntlMessages id="workflows.log-cancel-send-comment" />}
                      </button>
                    </>
                  )}
                  {onSubmit && (
                    <>
                      <button
                        className={classnames('cancel-button', styles['controls__send-button'])}
                        onClick={this.handleSubmit}
                        disabled={shouldSubmitAfterFileLoaded}
                      >
                        {submitIcon ? submitIcon : <IntlMessages id="workflows.log-send-comment" />}
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {children}
        </div>
        <AddLinkForm />
      </div>
    );
  }
}

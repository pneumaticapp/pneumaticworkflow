import React from 'react';
import classnames from 'classnames';
import {
  type LexicalNode,
  type NodeKey,
  type DOMConversionMap,
  type DOMConversionOutput,
  type DOMExportOutput,
  DecoratorNode,
  $applyNodeReplacement,
} from 'lexical';

import type { SerializedVariableNode, TVariableNodePayload } from './types';

import styles from './VariableNode.css';

// Constants
const VARIABLE_NODE_TYPE = 'variable';
const VARIABLE_NODE_VERSION = 1;
const VARIABLE_DATA_ATTRIBUTE = 'data-lexical-variable';
const VARIABLE_API_ATTRIBUTE = 'data-lexical-variable-api';
const VARIABLE_TITLE_ATTRIBUTE = 'data-lexical-variable-title';
const VARIABLE_SUBTITLE_ATTRIBUTE = 'data-lexical-variable-subtitle';
const LEXICAL_DECORATOR_ATTRIBUTE = 'data-lexical-decorator';



interface VariableComponentProps {
  apiName: string;
  title: string;
  subtitle?: string;
}

function VariableComponent({
  apiName,
  title,
  subtitle,
}: VariableComponentProps): React.ReactElement {
  return (
    <span
      className={classnames(styles['variable'], 'lexical-rich-editor-variable')}
      data-lexical-variable-api={apiName}
      data-lexical-variable-title={title}
      data-lexical-variable-subtitle={subtitle ?? ''}
    >
      {title || apiName}
    </span>
  );
}

/**
 * Lexical node representing a variable in the rich text editor.
 * Variables are displayed as styled spans with API name and title information.
 */
export class VariableNode extends DecoratorNode<React.ReactElement> {
  private readonly variableApiName: string;

  private readonly variableTitle: string;

  private readonly variableSubtitle?: string;

  /**
   * Returns the node type identifier.
   */
  static getType(): string {
    return VARIABLE_NODE_TYPE;
  }

  /**
   * Creates a clone of the variable node.
   */
  static clone(node: VariableNode): VariableNode {
    return new VariableNode(
      node.variableApiName,
      node.variableTitle,
      node.variableSubtitle,
      node.getKey(),
    );
  }

  /**
   * Imports a variable node from serialized JSON data.
   */
  static importJSON(serialized: SerializedVariableNode): VariableNode {
    return $createVariableNode({
      apiName: serialized.apiName,
      title: serialized.title,
      subtitle: serialized.subtitle,
    });
  }

  /**
   * Creates a new VariableNode instance.
   * @param apiName - The API name of the variable
   * @param title - The display title of the variable
   * @param subtitle - Optional subtitle for the variable
   * @param key - Optional node key
   */
  constructor(
    apiName: string,
    title: string,
    subtitle?: string,
    key?: NodeKey,
  ) {
    super(key);
    this.variableApiName = apiName;
    this.variableTitle = title;
    this.variableSubtitle = subtitle;
  }

  /**
   * Returns the API name of the variable.
   */
  getApiName(): string {
    return this.variableApiName;
  }

  /**
   * Returns the display title of the variable.
   */
  getTitle(): string {
    return this.variableTitle;
  }

  /**
   * Returns the optional subtitle of the variable.
   */
  getSubtitle(): string | undefined {
    return this.variableSubtitle;
  }

  /**
   * Indicates that this node should be treated as inline content.
   */
  // eslint-disable-next-line class-methods-use-this
  isInline(): boolean {
    return true;
  }

  /**
   * Returns the text content representation of the variable for serialization.
   */
  getTextContent(): string {
    return `{{${this.variableApiName}}}`;
  }

  /**
   * Defines how to convert DOM elements back to VariableNode instances.
   */
  static importDOM(): DOMConversionMap<HTMLSpanElement> | null {
    return {
      span: (domNode: HTMLSpanElement) => {
        if (!domNode.hasAttribute(VARIABLE_DATA_ATTRIBUTE)) return null;
        return {
          conversion: VariableNode.convertElementToNode,
          priority: 2,
        };
      },
    };
  }

  /**
   * Converts a DOM span element to a VariableNode.
   */
  private static convertElementToNode(element: HTMLSpanElement): DOMConversionOutput {
    const apiName = element.getAttribute(VARIABLE_API_ATTRIBUTE) ?? '';
    const title = element.getAttribute(VARIABLE_TITLE_ATTRIBUTE) ?? apiName;
    const subtitle = element.getAttribute(VARIABLE_SUBTITLE_ATTRIBUTE);

    return {
      node: $createVariableNode({
        apiName,
        title,
        subtitle: subtitle ?? undefined,
      }),
    };
  }

  /**
   * Creates a span element with variable attributes.
   * @param includeVariableData - Whether to include variable-specific data attributes
   */
  private createVariableSpanElement(includeVariableData: boolean): HTMLSpanElement {
    const span = document.createElement('span');
    span.setAttribute(LEXICAL_DECORATOR_ATTRIBUTE, this.getType());

    if (includeVariableData) {
      span.setAttribute(VARIABLE_DATA_ATTRIBUTE, 'true');
      span.setAttribute(VARIABLE_API_ATTRIBUTE, this.variableApiName);
      span.setAttribute(VARIABLE_TITLE_ATTRIBUTE, this.variableTitle);
      if (this.variableSubtitle != null) {
        span.setAttribute(VARIABLE_SUBTITLE_ATTRIBUTE, this.variableSubtitle);
      }
    }

    return span;
  }

  /**
   * Exports the node to a DOM element for rendering.
   */
  exportDOM(): DOMExportOutput {
    const span = this.createVariableSpanElement(true);
    span.textContent = this.variableTitle || this.variableApiName;
    return { element: span };
  }

  /**
   * Exports the node to JSON for serialization.
   */
  exportJSON(): SerializedVariableNode {
    return {
      type: VARIABLE_NODE_TYPE,
      version: VARIABLE_NODE_VERSION,
      apiName: this.variableApiName,
      title: this.variableTitle,
      subtitle: this.variableSubtitle,
    };
  }

  /**
   * Creates the DOM element that will contain the decorated content.
   */
  createDOM(): HTMLElement {
    return this.createVariableSpanElement(false);
  }

  /**
   * Since VariableNode content is static and doesn't change, always return false.
   */
  // eslint-disable-next-line class-methods-use-this
  updateDOM(): false {
    return false;
  }

  /**
   * Returns the React component to render for this decorator node.
   */
  decorate(): React.ReactElement {
    return (
      <VariableComponent
        apiName={this.variableApiName}
        title={this.variableTitle}
        subtitle={this.variableSubtitle}
      />
    );
  }
}

/**
 * Creates a new VariableNode with the provided payload data.
 * @param payload - The payload containing variable information
 * @returns A new VariableNode instance
 */
export function $createVariableNode(payload: TVariableNodePayload): VariableNode {
  const title = payload.title ?? payload.apiName;
  return $applyNodeReplacement(
    new VariableNode(payload.apiName, title, payload.subtitle),
  );
}

/**
 * Type guard to check if a node is a VariableNode.
 * @param node - The node to check
 * @returns True if the node is a VariableNode, false otherwise
 */
export function $isVariableNode(
  node: LexicalNode | null | undefined,
): node is VariableNode {
  return node instanceof VariableNode;
}

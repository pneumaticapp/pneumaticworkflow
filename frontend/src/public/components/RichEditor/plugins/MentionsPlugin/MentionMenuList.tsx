import React, { memo, useRef, useEffect, useState } from 'react';
import type { MentionMenuOption } from './types';
import styles from './MentionsPlugin.css';

type MentionMenuListProps = {
  rect: DOMRect;
  options: MentionMenuOption[];
  highlightedIndex: number;
  onSelect: (option: MentionMenuOption) => void;
  onHighlight: (index: number) => void;
};

function MentionMenuListComponent({
  rect,
  options,
  highlightedIndex,
  onSelect,
  onHighlight,
}: MentionMenuListProps): React.ReactElement {
  const menuRef = useRef<HTMLDivElement>(null);
  const optionRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => setVisible(true));
    });
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    const el = optionRefs.current[highlightedIndex];
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [highlightedIndex]);

  return (
    <div
      ref={menuRef}
      className={`${styles.menu} ${visible ? styles['menu-visible'] : ''}`}
      role="listbox"
      tabIndex={0}
      aria-activedescendant={
        options[highlightedIndex] ? `mention-option-${options[highlightedIndex].key}` : undefined
      }
      style={{
        position: 'fixed',
        top: rect.bottom + 4,
        left: rect.left,
        zIndex: 10,
      }}
      onMouseDown={(e) => e.preventDefault()}
    >
      {options.map((option, index) => (
        <button
          ref={(node) => {
            optionRefs.current[index] = node;
          }}
          key={option.key}
          id={`mention-option-${option.key}`}
          type="button"
          role="option"
          aria-selected={highlightedIndex === index}
          className={styles['item']}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => onSelect(option)}
          onMouseEnter={() => onHighlight(index)}
        >
          {option.name}
        </button>
      ))}
    </div>
  );
}

export const MentionMenuList = memo(MentionMenuListComponent);

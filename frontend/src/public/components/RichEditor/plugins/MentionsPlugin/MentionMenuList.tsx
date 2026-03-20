import React, { memo, useRef, useEffect, useLayoutEffect, useState } from 'react';
import type { MentionMenuOption } from './types';
import { getPositionRelativeToParent } from './getPositionRelativeToParent';
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
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useEffect(() => {
    let innerId: number | undefined;
    const outerId = requestAnimationFrame(() => {
      innerId = requestAnimationFrame(() => setVisible(true));
    });
    return () => {
      cancelAnimationFrame(outerId);
      if (innerId != null) cancelAnimationFrame(innerId);
    };
  }, []);

  useLayoutEffect(() => {
    setPosition(getPositionRelativeToParent(menuRef.current, rect));
  }, [rect]);

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
        top: position.top,
        left: position.left,
        zIndex: 1100,
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

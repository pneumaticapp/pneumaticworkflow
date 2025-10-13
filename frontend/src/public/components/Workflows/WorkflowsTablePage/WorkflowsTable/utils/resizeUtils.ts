import { debounce } from 'throttle-debounce';

const GLOBAL_COLUMNS_IDS = new Set(['workflow', 'templateName', 'starter', 'progress', 'step', 'performer']);
const startX = { current: 0 };
const startWidth = { current: 0 };
const resizingCol = { current: null as string | null };

const saveIntoLocalStorage = (widths: Record<string, number>, currentUserId: number, templateId: number) => {
  if (!currentUserId) return;
  const updatedWidths = { ...widths };

  const globalColumnWidths: Record<string, number> = {};

  GLOBAL_COLUMNS_IDS.forEach((id: string) => {
    if (updatedWidths[id]) {
      globalColumnWidths[id] = updatedWidths[id];
      delete updatedWidths[id];
    }
  });

  localStorage.setItem(`workflow-column-widths-${currentUserId}-global`, JSON.stringify(globalColumnWidths));
  if (templateId) {
    localStorage.setItem(
      `workflow-column-widths-${currentUserId}-template-${templateId}`,
      JSON.stringify(updatedWidths),
    );
  }
};

const debouncedSave = debounce(300, (widths: Record<string, number>, currentUserId: number, templateId: number) => {
  saveIntoLocalStorage(widths, currentUserId, templateId);
});

export const createResizeHandler = (
  colWidths: Record<string, number>,
  setColWidths: (widths: Record<string, number> | ((prev: Record<string, number>) => Record<string, number>)) => void,
  currentUserId: number,
  templateId: number,
) => {
  return (e: React.MouseEvent, colId: string, minWidth: number) => {
    startX.current = e.clientX;
    startWidth.current = colWidths[colId];
    resizingCol.current = colId;

    const handleMouseMove = (event: MouseEvent) => {
      if (!resizingCol.current) return;
      requestAnimationFrame(() => {
        const diff = event.clientX - startX.current;
        const newWidth = Math.max(startWidth.current + diff, minWidth);
        setColWidths((prev: Record<string, number>) => {
          const newWidths = { ...prev, [resizingCol.current!]: newWidth! };
          debouncedSave(newWidths, currentUserId, templateId);
          return newWidths;
        });
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      resizingCol.current = null;
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
};

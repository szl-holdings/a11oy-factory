/** Selection changes prefill a found receipt without discarding editable JSON on misses. */
export interface ReceiptSelection {
  hash: string | undefined;
  entries: readonly unknown[] | undefined;
  paste: string;
}

export function refreshReceiptSelection(
  previous: ReceiptSelection,
  hash: string | undefined,
  entries: readonly unknown[] | undefined,
  selected: unknown,
): ReceiptSelection {
  if (previous.hash === hash && previous.entries === entries) return previous;
  return {
    hash,
    entries,
    paste: selected ? JSON.stringify(selected, null, 2) : previous.paste,
  };
}

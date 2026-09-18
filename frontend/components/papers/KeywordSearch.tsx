"use client";

import { useEffect, useId, useState } from "react";

type Props = {
  options: { value: string; count: number }[];
  value: string[];
  onChange: (value: string[]) => void;
};

const parse = (text: string) => [...new Set(text.split(",").map((item) => item.trim()).filter(Boolean))];

export default function KeywordSearch({ options, value, onChange }: Props) {
  const [text, setText] = useState(value.join(", "));
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const listId = useId();
  useEffect(() => { setText(value.join(", ")); }, [value]);
  const parts = text.split(",");
  const term = (parts.pop() || "").trim().toLowerCase();
  const previous = parse(parts.join(","));
  const suggestions = options.filter((item) =>
    item.value.toLowerCase().includes(term) && !previous.some((keyword) => keyword.toLowerCase() === item.value.toLowerCase()),
  ).sort((a, b) => a.value.localeCompare(b.value)).slice(0, 20);

  function commit(next: string) {
    setText(next);
    onChange(parse(next));
    setOpen(false);
    setActive(-1);
  }
  function choose(keyword: string) { commit([...previous, keyword].join(", ")); }

  return (
    <div className="lib-keyword-search">
      <input
        className="lib-input-shell"
        type="search"
        placeholder="Keywords"
        aria-label="Keywords (comma-separated)"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={open && active >= 0 ? `${listId}-${active}` : undefined}
        value={text}
        onFocus={() => setOpen(true)}
        onBlur={() => commit(text)}
        onChange={(event) => {
          setText(event.target.value);
          setActive(-1);
          setOpen(true);
          if (!event.target.value) onChange([]);
        }}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            setOpen(true);
            setActive((index) => Math.max(0, Math.min(suggestions.length - 1, index + (event.key === "ArrowDown" ? 1 : -1))));
          } else if (event.key === "Enter") {
            event.preventDefault();
            if (open && active >= 0 && suggestions[active]) choose(suggestions[active].value);
            else commit(text);
          } else if (event.key === "Escape") {
            setOpen(false);
            setActive(-1);
          }
        }}
      />
      {open && (
        <ul className="lib-keyword-suggestions" id={listId} role="listbox">
          {suggestions.map((item, index) => (
            <li key={item.value} id={`${listId}-${index}`} role="option" aria-selected={index === active}>
              <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => choose(item.value)}>
                <span>{item.value}</span><span>{item.count}</span>
              </button>
            </li>
          ))}
          {!suggestions.length && <li className="lib-keyword-no-match" role="presentation">No matching keywords</li>}
        </ul>
      )}
    </div>
  );
}

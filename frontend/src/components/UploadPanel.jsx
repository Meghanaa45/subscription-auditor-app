import React, { useRef, useState } from "react";

export default function UploadPanel({ onFilesChosen, onUseSample, loading }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  function handleDrop(event) {
    event.preventDefault();
    setDragOver(false);
    if (event.dataTransfer.files.length) {
      onFilesChosen(Array.from(event.dataTransfer.files));
    }
  }

  return (
    <div className="upload-panel">
      <div
        className={`dropzone ${dragOver ? "dropzone--active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      >
        <span className="dropzone__label">Drop a bank CSV export here, or click to choose a file</span>
        <span className="dropzone__hint">Chase, Bank of America, Discover, or a plain date/description/amount CSV</span>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          multiple
          hidden
          onChange={(e) => e.target.files.length && onFilesChosen(Array.from(e.target.files))}
        />
      </div>
      <button className="link-button" onClick={onUseSample} disabled={loading}>
        {loading ? "Running audit\u2026" : "Or try it with sample data \u2192"}
      </button>
    </div>
  );
}

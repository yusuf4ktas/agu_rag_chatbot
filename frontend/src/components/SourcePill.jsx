import React from "react";

const SourcePill = ({ src }) => {
  // src: { source, page?, paragraph?, type?, lang? }
  const base = src.source || "Unknown source";
  const details = [];

  if (src.page != null) details.push(`p.${src.page}`);
  if (src.paragraph != null) details.push(`para ${src.paragraph}`);
  if (src.type) details.push(src.type);
  if (src.lang) details.push(src.lang.toUpperCase());

  const label = details.length > 0 ? `${base} • ${details.join(" • ")}` : base;

  const isLink =
    typeof src.source === "string" &&
    (src.source.startsWith("http://") || src.source.startsWith("https://"));

  const content = (
    <>
      <span className="dot" />
      <span className="source-label-text">{label}</span>
    </>
  );

  if (isLink) {
    return (
      <a
        href={src.source}
        target="_blank"
        rel="noopener noreferrer"
        className="pill"
        title={label}
      >
        {content}
      </a>
    );
  }

  return (
    <div className="pill" title={label}>
      {content}
    </div>
  );
};

export default SourcePill
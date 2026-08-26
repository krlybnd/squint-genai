import type { ChunkPreview } from "../../../api/types";
import { sanitizeText } from "@are/ui-core";

interface Props {
  title: string;
  chunks: ChunkPreview[];
  onOpenChunk?: (chunk: ChunkPreview) => void;
  openLabel: string;
  topKLabel: string;
  pageLabel: string;
}

export function ReasoningChunkList({
  title,
  chunks,
  onOpenChunk,
  openLabel,
  topKLabel,
  pageLabel,
}: Props) {
  if (chunks.length === 0) return null;
  return (
    <details className="reasoning-chunk-accordion">
      <summary>
        {title} ({chunks.length})
      </summary>
      <ul className="reasoning-chunk-list">
        {chunks.map((chunk) => (
          <li key={`${chunk.rank}-${chunk.chunk_id}`} className={chunk.selected ? "selected" : undefined}>
            <div className="reasoning-chunk-head">
              <span className="reasoning-chunk-rank">#{chunk.rank ?? "?"}</span>
              {chunk.selected && <span className="reasoning-chunk-badge">{topKLabel}</span>}
              {chunk.score != null && (
                <span className="reasoning-chunk-score">{Number(chunk.score).toFixed(3)}</span>
              )}
              <span className="reasoning-chunk-source">
                {sanitizeText(chunk.source_file || "doc")} {pageLabel}
                {chunk.page ?? "?"}
              </span>
              {onOpenChunk && chunk.chunk_id && (
                <button
                  type="button"
                  className="reasoning-chunk-open"
                  onClick={() => onOpenChunk(chunk)}
                >
                  {openLabel}
                </button>
              )}
            </div>
            {chunk.excerpt && <p className="reasoning-chunk-excerpt">{sanitizeText(chunk.excerpt)}</p>}
          </li>
        ))}
      </ul>
    </details>
  );
}

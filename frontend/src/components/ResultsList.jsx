// File: frontend/src/components/ResultsList.jsx
import React from 'react'

export default function ResultsList({ results = [], onSelect }) {
  // Safeguard: results default to empty array and ensure it's an array
  if (!Array.isArray(results) || results.length === 0) {
    return <p className="text-muted">No results found.</p>
  }

  return (
    <div className="row">
      {results.map(({ id, source, highlight }) => (
        <div key={id} className="col-md-6 mb-3">
          <div className="card h-100">
            <div className="card-body">
              <h5
                className="card-title"
                style={{ cursor: 'pointer' }}
                onClick={() => onSelect(id)}
              >
                {highlight?.title ? highlight.title[0] : source.title}
              </h5>
              <h6 className="card-subtitle mb-2 text-muted">
                {Array.isArray(source.authors) ? source.authors.join(', ') : ''} &mdash; {source.year}
              </h6>
              <p className="card-text">
                {highlight?.abstract
                  ? highlight.abstract[0]
                  : (source.abstract || '').substring(0, 200) + '...'}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
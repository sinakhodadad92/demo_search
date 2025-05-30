import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function DocModal({ id, onClose }) {
  const [doc, setDoc] = useState(null)

  useEffect(() => {
    axios.get(`http://localhost:8000/api/doc/${id}/`)
      .then((resp) => setDoc(resp.data.source))
      .catch(() => setDoc(null))
  }, [id])

  if (!doc) return null

  return (
    <div className="modal show d-block" tabIndex="-1">
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">{doc.title}</h5>
            <button type="button" className="btn-close" onClick={onClose} />
          </div>
          <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            <p><strong>Authors:</strong> {doc.authors.join(', ')}</p>
            <p><strong>Year:</strong> {doc.year}</p>
            <hr />
            <p>{doc.abstract}</p>
            <hr />
            <div>{doc.full_text}</div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
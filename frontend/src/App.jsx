// frontend/src/App.jsx
import React, { useState } from 'react'
import axios from 'axios'
import SearchBar from './components/SearchBar.jsx'
import ResultsList from './components/ResultsList.jsx'
import DocModal from './components/DocModal.jsx'

export default function App() {
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [searchTime, setSearchTime] = useState(0)
  const [lastQuery, setLastQuery] = useState('')
  const [suggestion, setSuggestion] = useState(null)
  const [selectedId, setSelectedId] = useState(null)

  const doSearch = async (q) => {
    setLastQuery(q)
    setSuggestion(null)
    const start = performance.now()
    try {
      const resp = await axios.get('/api/search/', {
        params: { q, page: 1, size: 10 }
      })
      const end = performance.now()
      setSearchTime(Math.round(end - start))
      setResults(resp.data.results)
      setTotal(resp.data.total)
      setSuggestion(resp.data.suggestion || null)
    } catch (err) {
      console.error('[App] Search error:', err)
      setResults([])
      setTotal(0)
      setSearchTime(0)
    }
  }

  return (
    <div className="container py-4">
      <h1 className="mb-4">SSOAR Search Demo</h1>
      <SearchBar onSearch={doSearch} />

      {lastQuery && (
        <p className="text-secondary">
          {total} result{total !== 1 ? 's' : ''} found in {searchTime} ms for '{lastQuery}'
        </p>
      )}

      {/* Suggestion UI */}
      {suggestion && total === 0 && (
        <p className="text-warning">
          Did you mean{' '}
          <a href="#" onClick={() => doSearch(suggestion)}>
            {suggestion}
          </a>
          ?
        </p>
      )}
      {suggestion && total > 0 && suggestion.toLowerCase() !== lastQuery.toLowerCase() && (
        <p className="text-info">
          Or search instead for{' '}
          <a href="#" onClick={() => doSearch(suggestion)}>
            {suggestion}
          </a>
        </p>
      )}

      <ResultsList results={results} onSelect={setSelectedId} />
      {selectedId && <DocModal id={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  )
}
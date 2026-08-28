import { Route, Routes } from 'react-router-dom'
import { SearchPage } from './pages/SearchPage'
import { ResultsPage } from './pages/ResultsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<SearchPage />} />
      <Route path="/results/:jobId" element={<ResultsPage />} />
    </Routes>
  )
}

export default App

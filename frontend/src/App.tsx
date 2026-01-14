import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StartPage from './components/StartPage';
import BenchmarkSystem from './components/BenchmarkSystem';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/benchmark" element={<BenchmarkSystem />} />
      </Routes>
    </Router>
  );
}

export default App;


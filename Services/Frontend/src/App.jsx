import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

import Dashboard from "./pages/Dashboard";

import ReadingsTable from "./components/ReadingsTable";

function App() {
  return <ReadingsTable />;
}

export default App;
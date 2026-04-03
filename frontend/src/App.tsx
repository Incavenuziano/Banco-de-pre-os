import { useState, useEffect } from "react";
import { Dashboard } from "./pages/Dashboard";
import { ComparativoItem } from "./pages/ComparativoItem";

function useHashRoute(): string {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const handler = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  return hash;
}

function App() {
  const hash = useHashRoute();

  if (hash === "#/comparar") {
    return <ComparativoItem />;
  }

  return <Dashboard />;
}

export default App;

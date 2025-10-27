import { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [health, setHealth] = useState<any>(null);
  const baseURL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    axios.get(`${baseURL}/health`, {
      headers: { "Idempotency-Key": "demo-key-123" }
    })
    .then(res => setHealth(res.data))
    .catch(err => setHealth({ error: String(err) }));
  }, [baseURL]);

  return (
    <div style={{fontFamily:"Inter, system-ui", padding:"2rem"}}>
      <h1>Slip Salary App — Frontend</h1>
      <p>API Base: {baseURL}</p>
      <pre>{JSON.stringify(health, null, 2)}</pre>
    </div>
  );
}

export default App;

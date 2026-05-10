import './base.css';
import BentoGrid from './components/BentoGrid';
import StatusStrip from './components/StatusStrip';
import { useWebSocket } from './hooks/useWebSocket';

export default function App() {
  useWebSocket();

  return (
    <div className="app">
      <BentoGrid />
      <StatusStrip />
    </div>
  );
}

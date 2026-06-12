import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

const MAX_FLOWS = 500;

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [flows, setFlows] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // For FastAPI standard websocket or python-socketio
    // Note: If using pure WebSockets in FastAPI, we'd use native WebSocket API instead of socket.io
    // Since we're using standard WebSocket in FastAPI (usually):
    
    let ws: WebSocket;
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/stream';
    let reconnectTimer: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'flow') {
            setFlows(prev => {
              const newFlows = [data.data, ...prev];
              if (newFlows.length > MAX_FLOWS) {
                return newFlows.slice(0, MAX_FLOWS);
              }
              return newFlows;
            });
          } else if (data.type === 'alert') {
            setAlerts(prev => [data.data, ...prev]);
          }
        } catch (e) {
          console.error('Error parsing WS message', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Reconnect after 3 seconds
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error', err);
        ws.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return { isConnected, flows, alerts };
}

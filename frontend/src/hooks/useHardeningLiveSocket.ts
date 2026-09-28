/**
 * Connexion WebSocket temps réel au dashboard de surveillance continue (module Hardening).
 * Relaie les événements agent_online/agent_offline/heartbeat (met à jour le cache React
 * Query des targets sans requête HTTP) et new_session (invalide sessions/targets + toast).
 * Reconnexion automatique avec backoff si la connexion tombe (réseau, redéploiement backend).
 */
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { buildHardeningDashboardWsUrl } from '@/api/client';

type LiveEvent = {
  type: 'agent_online' | 'agent_offline' | 'heartbeat' | 'new_session';
  target_id: string;
  at?: string;
  session_id?: string;
  score?: number;
  grade?: string;
  findings_summary?: Record<string, number>;
};

type TargetLike = {
  id: string;
  is_online: boolean;
  last_heartbeat_at: string | null;
};

const MIN_RECONNECT_DELAY = 2000;
const MAX_RECONNECT_DELAY = 30000;

export function useHardeningLiveSocket(enabled: boolean) {
  const queryClient = useQueryClient();
  const queryClientRef = useRef(queryClient);
  queryClientRef.current = queryClient;

  useEffect(() => {
    if (!enabled) return;

    let socket: WebSocket | null = null;
    let reconnectDelay = MIN_RECONNECT_DELAY;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closedByEffect = false;

    const patchTarget = (targetId: string, patch: Partial<TargetLike>) => {
      queryClientRef.current.setQueryData<TargetLike[]>(['hardening-targets'], (old) =>
        old?.map((t) => (t.id === targetId ? { ...t, ...patch } : t))
      );
    };

    const handleEvent = (event: LiveEvent) => {
      switch (event.type) {
        case 'agent_online':
          patchTarget(event.target_id, { is_online: true, last_heartbeat_at: event.at ?? null });
          break;
        case 'heartbeat':
          patchTarget(event.target_id, { is_online: true, last_heartbeat_at: event.at ?? null });
          break;
        case 'agent_offline':
          patchTarget(event.target_id, { is_online: false });
          break;
        case 'new_session':
          queryClientRef.current.invalidateQueries({ queryKey: ['hardening-sessions'] });
          queryClientRef.current.invalidateQueries({ queryKey: ['hardening-targets'] });
          toast.success(
            `Nouveau rapport reçu — score ${event.score ?? '?'}/100 (${event.grade ?? '?'})`,
            { duration: 5000 }
          );
          break;
      }
    };

    const connect = () => {
      const url = buildHardeningDashboardWsUrl();
      if (!url) return;

      socket = new WebSocket(url);

      socket.onopen = () => {
        reconnectDelay = MIN_RECONNECT_DELAY;
      };

      socket.onmessage = (msg) => {
        try {
          handleEvent(JSON.parse(msg.data) as LiveEvent);
        } catch {
          // Message non-JSON ignoré — ne doit jamais interrompre la connexion live.
        }
      };

      socket.onclose = () => {
        if (closedByEffect) return;
        reconnectTimer = setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    connect();

    return () => {
      closedByEffect = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [enabled]);
}

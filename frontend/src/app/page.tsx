"use client";

import { useEffect, useState } from "react";

type Analytics = { duration:number; current_people:number; peak_occupancy:number; unique_people:number; entries:number; exits:number; moving_percent:number; stationary_percent:number; fast_movements:number; average_tracking_time:number; most_common_direction:string };
type EventItem = { sequence:number; timestamp:string; type:string; person_id:number|null; value:string; message:string };

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const WS_URL = API_URL.replace(/^http/, "ws") + "/ws/events";

export default function Home() {
  const [analytics,setAnalytics] = useState<Analytics|null>(null);
  const [events,setEvents] = useState<EventItem[]>([]);
  const [backendOnline,setBackendOnline] = useState(false);
  const [cameraOnline,setCameraOnline] = useState(false);
  const [websocketOnline,setWebsocketOnline] = useState(false);
  const [currentTime,setCurrentTime] = useState("");

  useEffect(()=>{ const update=()=>setCurrentTime(new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"})); update(); const t=setInterval(update,1000); return()=>clearInterval(t); },[]);

  useEffect(()=>{
    let mounted=true;
    const fetchData=async()=>{ try{
      const [a,s]=await Promise.all([fetch(`${API_URL}/analytics`),fetch(`${API_URL}/status`)]);
      if(!a.ok||!s.ok) throw new Error("Backend unavailable");
      const ad=await a.json(); const sd=await s.json();
      if(!mounted)return; setAnalytics(ad); setBackendOnline(true); setCameraOnline(sd.camera==="ONLINE");
    }catch{ if(!mounted)return; setBackendOnline(false); setCameraOnline(false); } };
    fetchData(); const i=setInterval(fetchData,1000); return()=>{mounted=false;clearInterval(i)};
  },[]);

  useEffect(()=>{
    let socket:WebSocket|null=null; let timer:ReturnType<typeof setTimeout>|null=null; let cancelled=false;
    const connect=()=>{ if(cancelled)return; socket=new WebSocket(WS_URL);
      socket.onopen=()=>{if(!cancelled)setWebsocketOnline(true)};
      socket.onmessage=(message)=>{try{const event:EventItem=JSON.parse(message.data);setEvents(current=>current.some(x=>x.sequence===event.sequence)?current:[...current,event].slice(-30));}catch{console.error("Invalid event received.")}};
      socket.onclose=()=>{if(cancelled)return;setWebsocketOnline(false);timer=setTimeout(connect,2000)};
      socket.onerror=()=>setWebsocketOnline(false);
    };
    connect(); return()=>{cancelled=true;if(timer)clearTimeout(timer);if(socket)socket.close()};
  },[]);

  const people=analytics?.current_people??0, peak=analytics?.peak_occupancy??0, entries=analytics?.entries??0, exits=analytics?.exits??0;
  const moving=analytics?.moving_percent??0, fast=analytics?.fast_movements??0, avg=analytics?.average_tracking_time??0, direction=analytics?.most_common_direction||"N/A";

  return <main className="min-h-screen bg-[#070809] text-white">
    <header className="sticky top-0 z-50 border-b border-white/[0.08] bg-[#08090b]/95 backdrop-blur-xl"><div className="mx-auto flex h-[72px] max-w-[1600px] items-center justify-between px-5 sm:px-8">
      <div className="flex items-center gap-3"><div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold text-black">V<span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-emerald-400 ring-2 ring-[#08090b]"/></div><div><div className="flex items-center gap-2"><h1 className="text-[17px] font-semibold tracking-tight">VisionSense</h1><span className="hidden rounded bg-white/[0.06] px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-widest text-white/30 sm:block">AI</span></div><p className="text-[9px] uppercase tracking-[0.28em] text-white/30">Visual Intelligence</p></div></div>
      <div className="flex items-center gap-3 sm:gap-6"><div className="hidden text-right sm:block"><p className="text-[9px] uppercase tracking-[0.2em] text-white/25">System time</p><p className="mt-0.5 font-mono text-xs text-white/60">{currentTime}</p></div><div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.025] px-3 py-1.5"><span className={`h-1.5 w-1.5 rounded-full ${backendOnline?"bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]":"bg-red-400"}`}/><span className="text-[10px] font-medium uppercase tracking-wider text-white/65">{backendOnline?"Live":"Offline"}</span></div></div>
    </div></header>

    <div className="mx-auto max-w-[1600px] px-5 py-6 sm:px-8 sm:py-8">
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.7fr)_380px]">
        <div className="group relative overflow-hidden rounded-2xl border border-white/[0.09] bg-[#0d0f12] shadow-2xl">
          <div className="absolute left-0 right-0 top-0 z-20 flex items-center justify-between bg-gradient-to-b from-black/80 to-transparent px-5 py-5"><div className="flex items-center gap-2 rounded-full border border-white/10 bg-black/45 px-3 py-1.5 backdrop-blur-md"><span className="relative flex h-2 w-2">{cameraOnline&&<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-60"/>}<span className={`relative inline-flex h-2 w-2 rounded-full ${cameraOnline?"bg-red-500":"bg-white/20"}`}/></span><span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/80">Live Vision</span></div><div className="flex items-center gap-2"><div className="hidden rounded-md border border-white/10 bg-black/40 px-2.5 py-1.5 font-mono text-[9px] text-white/45 backdrop-blur sm:block">YOLO11n</div><div className="hidden rounded-md border border-white/10 bg-black/40 px-2.5 py-1.5 font-mono text-[9px] text-white/45 backdrop-blur sm:block">BYTETRACK</div></div></div>
          {cameraOnline?<div className="flex min-h-[420px] items-center justify-center bg-black lg:min-h-[560px]"><img src={`${API_URL}/video_feed`} alt="VisionSense live camera feed" className="h-auto max-h-[560px] w-full object-contain"/></div>:<div className="flex min-h-[420px] items-center justify-center lg:min-h-[560px]"><div className="text-center"><div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.025]"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" className="text-white/25"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="12" cy="12" r="3"/></svg></div><p className="text-sm font-medium text-white/45">Camera offline</p><p className="mt-1 text-xs text-white/20">Waiting for VisionSense engine</p></div></div>}
          <div className="flex items-center justify-between border-t border-white/[0.08] bg-[#0b0c0f] px-5 py-3"><div className="flex items-center gap-4"><span className="text-[10px] text-white/25">640 × 360</span><span className="hidden text-[10px] text-white/20 sm:block">Computer Vision Engine</span></div><div className="flex items-center gap-4"><span className="flex items-center gap-1.5 text-[9px] uppercase tracking-wider text-white/25"><span className={`h-1.5 w-1.5 rounded-full ${websocketOnline?"bg-emerald-400":"bg-white/15"}`}/>Events</span><span className="font-mono text-[9px] text-white/20">{websocketOnline?"WS CONNECTED":"WS OFFLINE"}</span></div></div>
        </div>

        <aside className="overflow-hidden rounded-2xl border border-white/[0.09] bg-[#0d0f12]"><div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4"><div><p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/40">Live Intelligence</p><p className="mt-1 text-[10px] text-white/20">Current scene analysis</p></div><span className="flex items-center gap-1.5 text-[9px] uppercase tracking-wider text-emerald-400/60"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400"/>Active</span></div>
          <div className="border-b border-white/[0.08] px-5 py-6"><p className="text-[9px] uppercase tracking-[0.2em] text-white/25">People detected</p><div className="mt-2 flex items-end justify-between"><span className="text-5xl font-semibold tracking-[-0.04em]">{people}</span><span className="pb-1 text-[10px] text-white/20">CURRENT</span></div></div>
          <div className="grid grid-cols-2"><MiniMetric label="Peak" value={peak}/><MiniMetric label="Entries" value={entries}/><MiniMetric label="Exits" value={exits}/><MiniMetric label="Track IDs" value={analytics?.unique_people??0}/></div>
          <div className="border-t border-white/[0.08] px-5 py-5"><div className="flex items-center justify-between"><p className="text-[10px] uppercase tracking-[0.18em] text-white/30">Scene movement</p><p className="font-mono text-xs text-white/65">{moving.toFixed(0)}%</p></div><div className="mt-3 h-1 overflow-hidden rounded-full bg-white/[0.08]"><div className="h-full rounded-full bg-white transition-all duration-700" style={{width:`${Math.min(moving,100)}%`}}/></div><div className="mt-2 flex justify-between text-[9px] text-white/20"><span>STATIONARY {analytics?.stationary_percent?.toFixed(0)??0}%</span><span>MOVING</span></div></div>
          <div className="border-t border-white/[0.08] px-5 py-5"><div className="flex items-center justify-between"><p className="text-[10px] uppercase tracking-[0.18em] text-white/30">Dominant direction</p><DirectionBadge direction={direction}/></div></div>
        </aside>
      </section>

      <section className="mt-5"><div className="mb-3 flex items-center justify-between"><p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/30">Session Overview</p><p className="font-mono text-[9px] text-white/20">LIVE SESSION</p></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><OverviewCard label="Session duration" value={`${analytics?.duration?.toFixed(0)??0}s`} detail="Since engine start"/><OverviewCard label="Fast movements" value={fast} detail="Detected movement events"/><OverviewCard label="Avg. tracking" value={`${avg.toFixed(1)}s`} detail="Per tracked subject"/><OverviewCard label="Most active direction" value={direction} detail="Based on movement events"/></div></section>

      <section className="mt-6 overflow-hidden rounded-2xl border border-white/[0.09] bg-[#0d0f12]"><div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4 sm:px-6"><div><div className="flex items-center gap-2"><p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/40">Activity Timeline</p><span className={`h-1.5 w-1.5 rounded-full ${websocketOnline?"bg-emerald-400":"bg-white/15"}`}/></div><p className="mt-1 text-[10px] text-white/20">Real-time intelligence events</p></div><div className="flex items-center gap-3"><span className="hidden font-mono text-[9px] text-white/20 sm:block">WEBSOCKET</span><span className="rounded-md border border-white/10 bg-white/[0.025] px-2 py-1 font-mono text-[9px] text-white/30">{events.length}</span></div></div><div className="max-h-[390px] overflow-y-auto">{events.length===0?<div className="flex min-h-[180px] items-center justify-center"><div className="text-center"><div className="mx-auto mb-3 h-1.5 w-1.5 animate-pulse rounded-full bg-white/30"/><p className="text-xs text-white/25">Waiting for activity...</p><p className="mt-1 text-[10px] text-white/15">VisionSense is monitoring the scene</p></div></div>:events.slice().reverse().map((event,index)=><EventRow key={event.sequence} event={event} latest={index===0}/>)}</div></section>

      <footer className="flex flex-col gap-2 py-6 text-[9px] uppercase tracking-[0.18em] text-white/15 sm:flex-row sm:items-center sm:justify-between"><span>VisionSense AI · Computer Vision Intelligence</span><span>YOLO11n · ByteTrack · FastAPI · Next.js</span></footer>
    </div>
  </main>;
}

function MiniMetric({label,value}:{label:string;value:number}){return <div className="border-b border-r border-white/[0.08] px-5 py-4 last:border-r-0"><p className="text-[9px] uppercase tracking-[0.18em] text-white/20">{label}</p><p className="mt-2 text-xl font-semibold tracking-tight text-white/80">{value}</p></div>}
function OverviewCard({label,value,detail}:{label:string;value:string|number;detail:string}){return <div className="group rounded-xl border border-white/[0.08] bg-[#0d0f12] px-5 py-5 transition hover:border-white/[0.14] hover:bg-[#0f1114]"><p className="text-[9px] uppercase tracking-[0.18em] text-white/25">{label}</p><p className="mt-3 text-2xl font-semibold tracking-[-0.02em] text-white/85">{value}</p><p className="mt-1 text-[9px] text-white/20">{detail}</p></div>}
function DirectionBadge({direction}:{direction:string}){const arrows:Record<string,string>={LEFT:"←",RIGHT:"→",UP:"↑",DOWN:"↓","N/A":"—"};return <span className="flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.035] px-2.5 py-1.5"><span className="text-sm text-white/65">{arrows[direction]??"•"}</span><span className="font-mono text-[9px] text-white/50">{direction}</span></span>}
function EventRow({event,latest}:{event:EventItem;latest:boolean}){const colors:Record<string,string>={PERSON_ENTERED:"bg-emerald-400",PERSON_EXITED:"bg-orange-400",FAST_MOVEMENT:"bg-red-400",MOVEMENT_STARTED:"bg-blue-400",MOVEMENT_STOPPED:"bg-white/40",DIRECTION_CHANGED:"bg-yellow-400",OCCUPANCY_CHANGE:"bg-purple-400",TRACK_LOST:"bg-white/25"};return <div className={`group flex items-start gap-4 border-b border-white/[0.05] px-5 py-4 transition hover:bg-white/[0.018] sm:px-6 ${latest?"bg-white/[0.012]":""}`}><div className="relative flex w-3 justify-center"><span className={`relative z-10 mt-1.5 h-1.5 w-1.5 rounded-full ${colors[event.type]??"bg-white/25"} ${latest?"shadow-[0_0_8px_rgba(255,255,255,0.25)]":""}`}/></div><div className="min-w-0 flex-1"><div className="flex items-start justify-between gap-3"><p className="text-xs leading-5 text-white/65 sm:text-sm">{event.message}</p>{event.person_id!==null&&<span className="hidden shrink-0 rounded border border-white/[0.08] px-2 py-1 font-mono text-[8px] text-white/20 sm:block">ID {event.person_id}</span>}</div><div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1"><span className="font-mono text-[9px] text-white/20">{event.timestamp}</span><span className="text-white/10">/</span><span className="font-mono text-[8px] uppercase tracking-wider text-white/15">{event.type}</span></div></div></div>}

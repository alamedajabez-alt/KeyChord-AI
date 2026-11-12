const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export interface Song { id:string; original_filename:string; duration:number; audio_format:string; size_bytes:number; created_at:string; }
function detailMessage(body:unknown,fallback:string){const detail=(body as {detail?:unknown}|null)?.detail;return typeof detail==="string"&&detail?detail:fallback;}
export function uploadSong(file:File,onProgress:(fraction:number)=>void,signal?:AbortSignal):Promise<Song>{return new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open("POST",`${BASE}/api/songs/upload`);xhr.responseType="json";xhr.upload.onprogress=e=>{if(e.lengthComputable&&e.total>0)onProgress(Math.min(e.loaded/e.total,1));};xhr.onload=()=>{if(xhr.status>=200&&xhr.status<300&&xhr.response)resolve(xhr.response as Song);else reject(new ApiError(xhr.status,detailMessage(xhr.response,"Upload failed. Please try again.")));};xhr.onerror=()=>reject(new ApiError(0,"Couldn't reach the server. Check that the API is running, then try again."));xhr.ontimeout=()=>reject(new ApiError(0,"The upload timed out. Please try again."));xhr.onabort=()=>reject(new DOMException("Upload cancelled","AbortError"));if(signal){if(signal.aborted)return reject(new DOMException("Upload cancelled","AbortError"));signal.addEventListener("abort",()=>xhr.abort(),{once:true});}const body=new FormData();body.append("file",file);xhr.send(body);});}

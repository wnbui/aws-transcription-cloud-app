"use client";
import { useState, useRef } from "react";

export default function Home() {
  const [recording, setRecording] = useState(false);
  const [audioURL, setAudioURL] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks: BlobPart[] = [];

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      const url = URL.createObjectURL(audioBlob);
      setAudioURL(url);

      const formData = new FormData();
      formData.append("audio", audioBlob);

      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setTranscription(data.transcription);
    };

    mediaRecorder.start();
    setRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const fetchTranscription = async () => {
    if (!jobId) return console.log("No transcription");
    const response = await fetch(`/api/transcribe?job_id=${jobId}`);
    const data = await response.json();
    setTranscription(data.transcriptUrl || "Processing...");
  };

  return (
    <div className="flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold">Audio Transcription</h1>
      <button
        className="btn btn-primary"
        onClick={recording ? stopRecording : startRecording}
      >
        {recording ? "Stop recording" : "Start recording"}
      </button>
      {audioURL && <audio src={audioURL} controls className="mt-4" />}
      {jobId && (
        <button className="btn btn-primary" onClick={fetchTranscription}>
          Transcription
        </button>
      )}
      {transcription && <div>{transcription}</div>}
    </div>
  );
}

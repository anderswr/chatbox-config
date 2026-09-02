export const REALTIME_MODELS = [
  { value: "gpt-realtime-2.1", label: "Nyeste samtalemodell (mest avansert)" },
  { value: "gpt-realtime-2.1-mini", label: "Nyeste lettmodell (rask og rimelig)" },
  { value: "gpt-realtime-2", label: "Avansert samtalemodell (grundig)" },
  { value: "gpt-realtime-1.5", label: "Tidligere samtalemodell (eldre)" },
  { value: "gpt-realtime", label: "Standard samtalemodell (anbefalt)" },
  { value: "gpt-realtime-mini", label: "Lett samtalemodell (rask)" },
];

export const REALTIME_VOICES = [
  { value: "marin", label: "Marin – anbefalt" },
  { value: "cedar", label: "Cedar – anbefalt" },
  { value: "alloy", label: "Alloy" },
  { value: "ash", label: "Ash" },
  { value: "ballad", label: "Ballad" },
  { value: "coral", label: "Coral" },
  { value: "echo", label: "Echo" },
  { value: "sage", label: "Sage" },
  { value: "shimmer", label: "Shimmer" },
  { value: "verse", label: "Verse" },
];

export const TRANSCRIPTION_MODELS = [
  { value: "gpt-realtime-whisper", label: "Direkte teksting (lav ventetid)" },
  { value: "gpt-4o-mini-transcribe", label: "Rask teksting (lett modell)" },
  { value: "gpt-4o-transcribe", label: "Nøyaktig teksting (høy kvalitet)" },
  { value: "whisper-1", label: "Klassisk teksting (eldre modell)" },
];

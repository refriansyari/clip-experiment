import { Loader2, Play, Scissors } from "lucide-react";
import type { ContentType, CropMode } from "../../types/clip.type";

type ControlPanelProps = {
  contentType: ContentType;
  cropMode: CropMode;
  error: string;
  isBusy: boolean;
  isSubmitting: boolean;
  maxDuration: number;
  minDuration: number;
  onContentTypeChange: (value: ContentType) => void;
  onCropModeChange: (mode: CropMode) => void;
  onMaxDurationChange: (value: number) => void;
  onMinDurationChange: (value: number) => void;
  onStartJob: () => void;
  onUrlChange: (value: string) => void;
  onUseLlmChange: (value: boolean) => void;
  url: string;
  useLlm: boolean;
};

export function ControlPanel({
  contentType,
  cropMode,
  error,
  isBusy,
  isSubmitting,
  maxDuration,
  minDuration,
  onContentTypeChange,
  onCropModeChange,
  onMaxDurationChange,
  onMinDurationChange,
  onStartJob,
  onUrlChange,
  onUseLlmChange,
  url,
  useLlm,
}: ControlPanelProps) {
  const isStartDisabled = isSubmitting || isBusy || !url.trim();
  const isProcessing = isSubmitting || isBusy;

  return (
    <section className="panel controlPanel">
      <div className="panelHeader">
        <Scissors size={20} />
        <h2>Clip YouTube Video</h2>
      </div>

      <label className="field wide">
        <span>YouTube Video URL</span>
        <input
          value={url}
          onChange={(event) => onUrlChange(event.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          required
        />
        <p className="field-help">Make sure the video has clear speech for best transcription results.</p>
      </label>

      <div className="segmentedField">
        <span>Content Type</span>
        <div className="segmentedControl" role="group" aria-label="Content type">
          {(["podcast", "football", "gaming"] as ContentType[]).map((type) => (
            <button
              key={type}
              className={contentType === type ? "active" : ""}
              type="button"
              onClick={() => onContentTypeChange(type)}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="segmentedField">
        <span>Scoring</span>
        <div className="segmentedControl" role="group" aria-label="Scoring method">
          <button
            className={!useLlm ? "active" : ""}
            type="button"
            onClick={() => onUseLlmChange(false)}
          >
            Heuristic
          </button>
          <button
            className={useLlm ? "active" : ""}
            type="button"
            onClick={() => onUseLlmChange(true)}
          >
            AI (OpenRouter)
          </button>
        </div>
      </div>

      <div className="gridFields">
        <label className="field">
          <span>Min Duration (s)</span>
          <input
            min={5}
            max={600}
            type="number"
            value={minDuration}
            onChange={(event) => onMinDurationChange(Number(event.target.value))}
          />
        </label>
        <label className="field">
          <span>Max Duration (s)</span>
          <input
            min={10}
            max={600}
            type="number"
            value={maxDuration}
            onChange={(event) => onMaxDurationChange(Number(event.target.value))}
          />
        </label>
      </div>

      <div className="segmentedField">
        <span>Crop Mode</span>
        <div className="segmentedControl" role="group" aria-label="Video crop mode">
          <button
            className={cropMode === "center" ? "active" : ""}
            type="button"
            onClick={() => onCropModeChange("center")}
          >
            Center
          </button>
          <button
            className={cropMode === "person" ? "active" : ""}
            type="button"
            onClick={() => onCropModeChange("person")}
          >
            Follow Person
          </button>
          <button
            className={cropMode === "letterbox" ? "active" : ""}
            type="button"
            onClick={() => onCropModeChange("letterbox")}
          >
            Letterbox
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <button className="primary" type="button" disabled={isStartDisabled} onClick={onStartJob}>
        {isProcessing ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
        {isProcessing ? "Processing..." : "Start Clipping"}
      </button>
    </section>
  );
}

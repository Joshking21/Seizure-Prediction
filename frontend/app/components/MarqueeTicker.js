"use client";

export default function MarqueeTicker() {
  const items = [
    "REAL-TIME SEIZURE PREDICTION",
    "18-CHANNEL CHB-MIT MONTAGE",
    "DUAL-STREAM CNN-LSTM",
    "256 HZ EEG HARMONIZATION",
    "DAUBECHIES-4 DWT SUB-BANDS",
    "SUB-40MS INFERENCE LATENCY",
    "PRE-ICTAL EARLY WARNING SYSTEM",
    "PHYSIOLOGICAL SYNCHRONY DETECTION",
    "FUTO COMPUTER SCIENCE PROJECT",
  ];

  return (
    <div className="editorial-marquee-wrap">
      <div className="editorial-marquee-track">
        {/* Sequence 1 */}
        <div className="editorial-marquee-content">
          {items.map((item, idx) => (
            <div key={`m1-${idx}`} className="editorial-marquee-item">
              <span>{item}</span>
              <span className="marquee-dot"></span>
            </div>
          ))}
        </div>
        {/* Sequence 2 for continuous seamless loop */}
        <div className="editorial-marquee-content" aria-hidden="true">
          {items.map((item, idx) => (
            <div key={`m2-${idx}`} className="editorial-marquee-item">
              <span>{item}</span>
              <span className="marquee-dot"></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import "./globals.css";

export const metadata = {
  title: "NeuroGuard — Seizure Prediction Dashboard",
  description:
    "Real-time EEG seizure prediction dashboard powered by a Dual-Stream CNN-LSTM model. FUTO Final Year Project.",
  keywords: ["seizure prediction", "EEG", "deep learning", "CNN-LSTM", "FUTO"],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", margin: 0, background: "#090b0f", color: "#e8edf3" }}>
        {children}
      </body>
    </html>
  );
}

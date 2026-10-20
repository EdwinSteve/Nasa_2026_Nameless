import type { Metadata } from "next";
import { Nunito, Nunito_Sans } from "next/font/google";
import "./globals.css";

const nunito = Nunito_Sans({
  variable: "--font-nunito",
  subsets: ["latin"],
});

// Títulos de la bienvenida
const nunitoTitulo = Nunito({
  variable: "--font-nunito-titulo",
  subsets: ["latin"],
  weight: ["700", "800", "900"],
});

export const metadata: Metadata = {
  title: "SURCO",
  description: "Recomendaciones de rotación de cultivos con datos NASA para fincas del Huila",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={`${nunito.variable} ${nunitoTitulo.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}

import "pdfjs-dist/web/pdf_viewer.css";
import "../../library/library.css";
import "./paper-detail.css";
import PaperDetailClient from "./PaperDetailClient";

type PaperDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function PaperDetailPage({ params }: PaperDetailPageProps) {
  const { id } = await params;
  return <PaperDetailClient id={id} />;
}

/**
 * Exports côté client uniquement (aucun envoi) : PNG d'un graphique, PDF de la page de résultats.
 * Les bibliothèques sont chargées à la demande pour ne pas alourdir le chargement initial.
 */
function download(dataUrl: string, fileName: string) {
  const a = document.createElement('a');
  a.href = dataUrl;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

/** Fond blanc explicite : lu dans les tokens pour ne pas introduire de couleur littérale. */
const pageBackground = () => getComputedStyle(document.documentElement).getPropertyValue('--color-white').trim();

export async function exportNodePng(node: HTMLElement, fileName: string): Promise<void> {
  const { toPng } = await import('html-to-image');
  download(await toPng(node, { pixelRatio: 2, backgroundColor: pageBackground(), cacheBust: false }), `${fileName}.png`);
}

export async function exportNodePdf(node: HTMLElement, fileName: string): Promise<void> {
  const [{ toPng }, { jsPDF }] = await Promise.all([import('html-to-image'), import('jspdf')]);
  const png = await toPng(node, { pixelRatio: 1.5, backgroundColor: pageBackground() });
  const img = new Image();
  img.src = png;
  await img.decode();
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageW = 210, pageH = 297, margin = 10;
  const w = pageW - 2 * margin;
  const h = (img.height * w) / img.width;
  const usable = pageH - 2 * margin;
  for (let y = 0, page = 0; y < h; y += usable, page++) {
    if (page) pdf.addPage();
    pdf.addImage(png, 'PNG', margin, margin - y, w, h);
  }
  pdf.save(`${fileName}.pdf`);
}

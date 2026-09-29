import type { Meta } from '../domain/schemas';

export const frDate = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });

/** Bandeau permanent sur l'état des données candidat·es. */
export function DataBanner({ meta }: { meta: Meta }) {
  return (
    <p className="data-banner" role="note">
      Programmes 2027 encore incomplets au {frDate(meta.dataDate)} ; résultats indicatifs, ce n'est pas une consigne de vote.
    </p>
  );
}
